import math
import unittest
import warnings
from unittest import mock
from unittest.mock import MagicMock

from machinelogic.ivention.exception import RobotException
from machinelogic.ivention.irobot import (
    RobotOperationalState,
    RobotSafetyState,
)
from machinelogic.machinelogic.robot.robot import (
    Robot,
    RobotState,
    RosRobotSingleton,
    log_alarm_callback,
    parse_ros_address,
    round_array_elements,
)
from machinelogic.machinelogic.robot.vention_ros_client_library import (
    RobotAlarm,
    RosRobotClient,
)


class TestRoundArrayElements(unittest.TestCase):
    def test_round_array_elements_default_digits(self) -> None:
        array = [1.234, 2.567, 3.999]
        expected = [1.23, 2.57, 4.0]
        self.assertEqual(round_array_elements(array), expected)

    def test_round_array_elements_custom_digits(self) -> None:
        array = [1.234, 2.567, 3.999]
        expected = [1.2, 2.6, 4.0]
        self.assertEqual(round_array_elements(array, 1), expected)


class TestParseRosAddress(unittest.TestCase):
    def test_parse_ros_address_with_ws(self) -> None:
        ros_url = "ws://localhost:9090"
        address = parse_ros_address(ros_url)
        self.assertEqual(address.host, "localhost")
        self.assertEqual(address.port, 9090)

    def test_parse_ros_address_with_wss(self) -> None:
        ros_url = "wss://example.com/robot/1234"
        address = parse_ros_address(ros_url)
        self.assertEqual(address.host, f"{ros_url}:1234")
        self.assertIsNone(address.port)

    def test_parse_ros_address_with_wss_no_port(self) -> None:
        ros_url = "wss://example.com/robot/abc"
        address = parse_ros_address(ros_url)
        self.assertEqual(address.host, "example.com")
        self.assertIsNone(address.port)


class TestLogAlarmCallback(unittest.TestCase):
    def test_log_alarm_callback_with_error_exception(self) -> None:
        alarm = RobotAlarm(RobotAlarm.Level.ERROR, 1, "Test error")
        with self.assertRaises(RobotException):
            log_alarm_callback(alarm)

    def test_log_alarm_callback_with_warning_no_exception(self) -> None:
        alarm = RobotAlarm(RobotAlarm.Level.WARNING, 1, "Test warning")
        # Should not raise exception but print warning
        with mock.patch("builtins.print") as mock_print:
            log_alarm_callback(alarm)
            mock_print.assert_called_once()

    def test_log_alarm_callback_with_custom_levels(self) -> None:
        alarm = RobotAlarm(RobotAlarm.Level.WARNING, 1, "Test warning")
        # Should raise exception when warning level is set to trigger exception
        with self.assertRaises(RobotException):
            log_alarm_callback(alarm, exception_alarm_level=RobotAlarm.Level.WARNING)


class TestRosRobotSingleton(unittest.TestCase):
    @mock.patch("machinelogic.machinelogic.robot.robot.RosRobotClient")
    def test_singleton_pattern(self, mock_ros_robot_class: MagicMock) -> None:
        mock_instance = mock.MagicMock()
        mock_ros_robot_class.return_value = mock_instance

        # Reset the singleton to ensure a clean test
        RosRobotSingleton.__instance = None

        instance1 = RosRobotSingleton.get_instance("ws://localhost:9090")
        instance2 = RosRobotSingleton.get_instance("ws://localhost:9090")
        self.assertIs(instance1, instance2)

    @mock.patch("machinelogic.machinelogic.robot.robot.RosRobotClient")
    def test_ip_address_override(self, mock_ros_robot: MagicMock) -> None:
        # Reset singleton
        RosRobotSingleton.__instance = None

        RosRobotSingleton.get_instance("ws://localhost:9090", ip_address_override="192.168.1.1")
        mock_ros_robot.assert_called_once()
        args, kwargs = mock_ros_robot.call_args
        self.assertEqual(kwargs["pendant_ip"], "192.168.1.1")


class TestRobotState(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_robot = mock.MagicMock()
        self.mock_api = mock.MagicMock()
        self.mock_config = mock.MagicMock()
        self.robot_state = RobotState(self.mock_robot, self.mock_api, self.mock_config)

    def test_cartesian_position(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message="cartesian_position is deprecated",
            )
            self.mock_robot.get_cartesian_position.return_value = (
                [100.123, 200.456, 300.789, 0.0, 90.0, 180.0],
                12345,
            )
            position = self.robot_state.cartesian_position
            self.assertEqual(position, [100.12, 200.46, 300.79, 0.0, 90.0, 180.0])

    def test_joint_angles(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message="joint_angles is deprecated",
            )
            self.mock_robot.get_joint_positions.return_value = (
                [10.123, 20.456, 30.789, 40.123, 50.456, 60.789],
                12345,
            )
            angles = self.robot_state.joint_angles
            self.assertEqual(angles, [10.12, 20.46, 30.79, 40.12, 50.46, 60.79])

    def test_cartesian_position_data(self) -> None:
        timestamp = 12345
        self.mock_robot.get_cartesian_position.return_value = (
            [100.123, 200.456, 300.789, 0.0, 90.0, 180.0],
            timestamp,
        )
        position, ts = self.robot_state.cartesian_position_data
        self.assertEqual(position, [100.12, 200.46, 300.79, 0.0, 90.0, 180.0])
        self.assertEqual(ts, timestamp)

    def test_joint_angles_data(self) -> None:
        timestamp = 12345
        self.mock_robot.get_joint_positions.return_value = (
            [10.123, 20.456, 30.789, 40.123, 50.456, 60.789],
            timestamp,
        )
        angles, ts = self.robot_state.joint_angles_data
        self.assertEqual(angles, [10.12, 20.46, 30.79, 40.12, 50.46, 60.79])
        self.assertEqual(ts, timestamp)

    def test_operational_state(self) -> None:
        self.mock_robot.get_robot_state.return_value = RobotOperationalState.NORMAL
        state = self.robot_state.operational_state
        self.assertEqual(state, RobotOperationalState.NORMAL)

    def test_safety_state(self) -> None:
        self.mock_robot.get_safety_state.return_value = RobotSafetyState.NORMAL
        state = self.robot_state.safety_state
        self.assertEqual(state, RobotSafetyState.NORMAL)

    def test_move_in_progress(self) -> None:
        self.mock_robot.get_move_in_progress.return_value = True
        self.assertTrue(self.robot_state.move_in_progress)

        self.mock_robot.get_move_in_progress.return_value = False
        self.assertFalse(self.robot_state.move_in_progress)

    def test_tcp_offset(self) -> None:
        # Mock the active TCP dictionary structure that the API returns
        mock_active_tcp = {
            "offset": {
                "x": 0.01,  # 10mm in meters
                "y": 0.02,  # 20mm in meters
                "z": 0.03,  # 30mm in meters
                "i": 0.0,  # 0 degrees in radians
                "j": math.pi / 2,  # 90 degrees in radians
                "k": math.pi,  # 180 degrees in radians
            }
        }

        # Mock the API call to get active TCP
        self.mock_api.get_active_tcp.return_value = mock_active_tcp
        self.mock_config.uuid = "test-robot-uuid"

        offset = self.robot_state.tcp_offset

        # Verify API call was made with correct robot UUID
        self.mock_api.get_active_tcp.assert_called_once_with("test-robot-uuid")

        self.assertEqual(offset[0], mock_active_tcp["offset"]["x"] * 1000)
        self.assertEqual(offset[1], mock_active_tcp["offset"]["y"] * 1000)
        self.assertEqual(offset[2], mock_active_tcp["offset"]["z"] * 1000)
        self.assertEqual(offset[3], mock_active_tcp["offset"]["i"] * 180 / math.pi)
        self.assertEqual(offset[4], mock_active_tcp["offset"]["j"] * 180 / math.pi)
        self.assertEqual(offset[5], mock_active_tcp["offset"]["k"] * 180 / math.pi)

    def test_active_tcp(self) -> None:
        # Mock the active TCP dictionary structure that the API returns
        mock_active_tcp = {"tcpUuid": "tcp-uuid-123"}

        # Mock the API call
        self.mock_api.get_active_tcp.return_value = mock_active_tcp
        self.mock_config.uuid = "test-robot-uuid"

        # Mock the TCP list in configuration
        mock_tcp_item = mock.MagicMock()
        mock_tcp_item.uuid = "tcp-uuid-123"
        mock_tcp_item.name = "gripper_tcp"
        self.mock_config.tcp_list = [mock_tcp_item]

        active_tcp_name = self.robot_state.active_tcp

        # Verify API call was made with correct robot UUID
        self.mock_api.get_active_tcp.assert_called_once_with("test-robot-uuid")

        # Verify the correct TCP name is returned
        self.assertEqual(active_tcp_name, "gripper_tcp")

    def test_active_tcp_not_found(self) -> None:
        # Mock the active TCP dictionary with UUID that doesn't match any TCP in config
        mock_active_tcp = {"tcpUuid": "nonexistent-tcp-uuid"}

        # Mock the API call
        self.mock_api.get_active_tcp.return_value = mock_active_tcp
        self.mock_config.uuid = "test-robot-uuid"

        # Mock empty TCP list
        self.mock_config.tcp_list = []

        active_tcp_name = self.robot_state.active_tcp

        # Should return None when TCP not found
        self.assertIsNone(active_tcp_name)

    def test_get_digital_input_value(self) -> None:
        self.mock_robot.get_tool_digital_input.return_value = 1
        self.assertTrue(self.robot_state.get_digital_input_value(1))

        self.mock_robot.get_tool_digital_input.return_value = 0
        self.assertFalse(self.robot_state.get_digital_input_value(2))


class TestRobot(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_ros_client = mock.MagicMock()
        self.mock_api = mock.MagicMock()
        self.mock_config = mock.MagicMock()

        # Setup configuration with required properties
        self.mock_config._ros_address = "ws://localhost:9090"
        self.mock_config.uuid = "test-uuid"

        # Mock the singleton to return our mock client
        patcher = mock.patch("machinelogic.machinelogic.robot.robot.RosRobotSingleton")
        self.mock_singleton = patcher.start()
        self.mock_singleton.get_instance.return_value = self.mock_ros_client
        self.addCleanup(patcher.stop)

        self.robot = Robot(self.mock_config, self.mock_api)

    def test_init(self) -> None:
        # Test that robot is initialized properly
        self.assertEqual(self.robot._configuration, self.mock_config)
        self.assertEqual(self.robot._robot, self.mock_ros_client)
        self.assertEqual(self.robot._api, self.mock_api)
        self.assertIsInstance(self.robot._state, RobotState)

    def test_state_property(self) -> None:
        self.assertIsInstance(self.robot.state, RobotState)

    def test_on_log_alarm(self) -> None:
        callback = mock.MagicMock()
        self.mock_ros_client.on_log_alarm.return_value = 123
        result = self.robot.on_log_alarm(callback)
        self.assertEqual(result, 123)
        self.mock_ros_client.on_log_alarm.assert_called_once_with(callback)

    def test_move_stop(self) -> None:
        self.mock_ros_client.move_stop.return_value = True
        result = self.robot.move_stop()
        self.assertTrue(result)
        self.mock_ros_client.move_stop.assert_called_once()

    def test_compute_forward_kinematics(self) -> None:
        joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.mock_ros_client.forward_kinematics.return_value = [
            100.123,
            200.456,
            300.789,
            0,
            90,
            180,
        ]
        result = self.robot.compute_forward_kinematics(joint_angles)
        self.assertEqual(result, [100.12, 200.46, 300.79, 0, 90, 180])

    def test_compute_forward_kinematics_invalid_input(self) -> None:
        joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0]  # Only 5 angles instead of 6
        with self.assertRaises(ValueError):
            self.robot.compute_forward_kinematics(joint_angles)

    def test_compute_inverse_kinematics(self) -> None:
        cartesian_pose = [100.0, 200.0, 300.0, 0.0, 90.0, 180.0]
        self.mock_ros_client.inverse_kinematics.return_value = [
            10.123,
            20.456,
            30.789,
            40.123,
            50.456,
            60.789,
        ]
        result = self.robot.compute_inverse_kinematics(cartesian_pose)
        self.assertEqual(result, [10.12, 20.46, 30.79, 40.12, 50.46, 60.79])

    def test_set_tcp_offset(self) -> None:
        tcp_offset = [10.0, 20.0, 30.0, 45.0, 90.0, 180.0]
        self.mock_api.set_tcp_offset.return_value = True

        result = self.robot.set_tcp_offset(tcp_offset)

        self.assertTrue(result)
        self.mock_api.set_tcp_offset.assert_called_once()

        # Check that the conversion to meters and radians was done correctly
        args, kwargs = self.mock_api.set_tcp_offset.call_args
        tcp_offset_payload = args[1]

        # First 3 elements should be converted to meters (divide by 1000)
        self.assertAlmostEqual(tcp_offset_payload[0], 0.01)  # 10/1000
        self.assertAlmostEqual(tcp_offset_payload[1], 0.02)  # 20/1000
        self.assertAlmostEqual(tcp_offset_payload[2], 0.03)  # 30/1000

        # Last 3 elements should be converted to radians
        self.assertAlmostEqual(tcp_offset_payload[3], math.radians(45))
        self.assertAlmostEqual(tcp_offset_payload[4], math.radians(90))
        self.assertAlmostEqual(tcp_offset_payload[5], math.radians(180))

    def test_set_tcp_offset_is_deprecated(self) -> None:
        tcp_offset = [10.0, 20.0, 30.0, 45.0, 90.0, 180.0]
        with warnings.catch_warnings(record=True) as warnings_list:
            self.robot.set_tcp_offset(tcp_offset)
            self.assertEqual(len(warnings_list), 1)
            self.assertTrue(issubclass(warnings_list[-1].category, DeprecationWarning))
            self.assertIn("set_tcp_offset is deprecated", str(warnings_list[-1].message))

    def test_reset(self) -> None:
        self.mock_ros_client.reset.return_value = {"success": True}
        result = self.robot.reset()
        self.assertTrue(result)
        self.mock_ros_client.reset.assert_called_once()

    def test_set_tool_digital_output(self) -> None:
        self.mock_ros_client.set_tool_digital_output.return_value = {"success": True}
        result = self.robot.set_tool_digital_output(1, 1)
        self.assertTrue(result)
        self.mock_ros_client.set_tool_digital_output.assert_called_once_with(1, 1)

    def test_set_payload(self) -> None:
        self.mock_ros_client.set_payload.return_value = {"success": True}
        result = self.robot.set_payload(2.5)
        self.assertTrue(result)
        self.mock_ros_client.set_payload.assert_called_once_with(2.5)

    def test_set_active_tcp_success(self) -> None:
        # Mock TCP configuration
        mock_tcp = mock.MagicMock()
        mock_tcp.name = "gripper_tcp"
        mock_tcp.uuid = "tcp-uuid-123"
        self.mock_config.tcp_list = [mock_tcp]
        self.mock_config.uuid = "robot-uuid"

        # Mock successful API call
        self.mock_api.set_active_tcp.return_value = True

        # Test the method
        self.robot.set_active_tcp("gripper_tcp")

        # Verify API was called with correct parameters
        self.mock_api.set_active_tcp.assert_called_once_with("robot-uuid", "tcp-uuid-123")

    def test_set_active_tcp_not_found(self) -> None:
        # Mock empty TCP list
        self.mock_config.tcp_list = []

        # Test that RobotException is raised for non-existent TCP
        with self.assertRaises(RobotException) as context:
            self.robot.set_active_tcp("nonexistent_tcp")

        self.assertIn("TCP with name nonexistent_tcp not found", str(context.exception))

    def test_set_active_tcp_api_failure(self) -> None:
        # Mock TCP configuration
        mock_tcp = mock.MagicMock()
        mock_tcp.name = "gripper_tcp"
        mock_tcp.uuid = "tcp-uuid-123"
        self.mock_config.tcp_list = [mock_tcp]
        self.mock_config.uuid = "robot-uuid"

        # Mock failed API call
        self.mock_api.set_active_tcp.return_value = False

        # Test that RobotException is raised when API call fails
        with self.assertRaises(RobotException) as context:
            self.robot.set_active_tcp("gripper_tcp")

        self.assertIn("Failed to set active TCP to gripper_tcp", str(context.exception))

    def test_create_sequence(self) -> None:
        mock_sequence_builder = mock.MagicMock()
        self.mock_ros_client.create_sequence.return_value = mock_sequence_builder
        result = self.robot.create_sequence()
        self.assertEqual(result, mock_sequence_builder)

    def test_on_system_state_change(self) -> None:
        callback = mock.MagicMock()
        self.mock_ros_client.on_state_change.return_value = 456
        result = self.robot.on_system_state_change(callback)
        self.assertEqual(result, 456)
        self.mock_ros_client.on_state_change.assert_called_once_with(callback)

    def test_movej(self) -> None:
        target = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        velocity = 15.0
        acceleration = 20.0

        self.robot.movej(target, velocity, acceleration)

        self.mock_ros_client.movej.assert_called_once_with(target, velocity, acceleration)

    def test_movel(self) -> None:
        target = [100.0, 200.0, 300.0, 0.0, 90.0, 180.0]
        velocity = 150.0
        acceleration = 200.0
        reference_frame = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.robot.movel(target, velocity, acceleration, reference_frame)

        self.mock_ros_client.movel.assert_called_once_with(target, velocity, acceleration, reference_frame)

    def test_movej_async(self) -> None:
        target = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        velocity = 15.0
        acceleration = 20.0

        self.robot.movej_async(target, velocity, acceleration)

        self.mock_ros_client.movej.assert_called_once_with(target, velocity, acceleration, is_async=True)

    def test_movel_async(self) -> None:
        target = [100.0, 200.0, 300.0, 0.0, 90.0, 180.0]
        velocity = 150.0
        acceleration = 200.0
        reference_frame = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.robot.movel_async(target, velocity, acceleration, reference_frame)

        self.mock_ros_client.movel.assert_called_once_with(target, velocity, acceleration, reference_frame, is_async=True)

    def test_execute_sequence(self) -> None:
        # Create a mock that is an instance of RosRobotClient.SequenceBuilder
        mock_sequence = mock.MagicMock(spec=RosRobotClient.SequenceBuilder)
        self.mock_ros_client.execute_sequence.return_value = True

        result = self.robot.execute_sequence(mock_sequence)

        self.assertTrue(result)
        self.mock_ros_client.execute_sequence.assert_called_once_with(mock_sequence)

    def test_execute_sequence_with_invalid_type(self) -> None:
        # Create a mock that is not an instance of RosRobotClient.SequenceBuilder
        mock_sequence = mock.MagicMock()

        with self.assertRaises(TypeError):
            self.robot.execute_sequence(mock_sequence)

    def test_execute_sequence_async(self) -> None:
        # Create a mock that is an instance of RosRobotClient.SequenceBuilder
        mock_sequence = mock.MagicMock(spec=RosRobotClient.SequenceBuilder)
        self.mock_ros_client.execute_sequence.return_value = True

        result = self.robot.execute_sequence_async(mock_sequence)

        self.assertTrue(result)
        self.mock_ros_client.execute_sequence.assert_called_once_with(mock_sequence, is_async=True)

    def test_wait_for_motion_completion(self) -> None:
        self.mock_ros_client.wait_for_motion_completion.return_value = True
        result = self.robot.wait_for_motion_completion(timeout=10.0)
        self.assertTrue(result)
        self.mock_ros_client.wait_for_motion_completion.assert_called_once_with(timeout=10.0)

    def test_teach_mode(self) -> None:
        mock_teach = mock.MagicMock()
        self.mock_ros_client.teach_mode.return_value = mock_teach
        result = self.robot.teach_mode()
        self.assertEqual(result, mock_teach)

    def test_reconnect(self) -> None:
        self.mock_api.reconnect_robot.return_value = True
        result = self.robot.reconnect(timeout=20.0)
        self.assertTrue(result)
        self.mock_api.reconnect_robot.assert_called_once_with(robot_uuid="test-uuid", timeout=20.0)


if __name__ == "__main__":
    unittest.main()
