import unittest
from unittest.mock import MagicMock

from machinelogic.ivention.exception import PathFollowingException
from machinelogic.machinelogic.path_follower import PathFollower


class TestPathFollower(unittest.TestCase):
    def setUp(self) -> None:
        # Arrange
        self.api_mock = MagicMock()

        self.start_path_spy = MagicMock()
        self.api_mock.start_path = self.start_path_spy

        self.stop_path_spy = MagicMock()
        self.api_mock.stop_path = self.stop_path_spy

        self.get_path_status_spy = MagicMock()
        self.api_mock.get_path_status = self.get_path_status_spy

        self.add_path_tool_spy = MagicMock()
        self.api_mock.add_path_tool = self.add_path_tool_spy

        self.set_path_axes_map_spy = MagicMock()
        self.api_mock.set_path_axes_map = self.set_path_axes_map_spy

        self.actuator_x_mock = MagicMock()
        self.actuator_y_mock = MagicMock()
        self.actuator_z_mock = MagicMock()
        for actuator_mock in [
            self.actuator_x_mock,
            self.actuator_y_mock,
            self.actuator_z_mock,
        ]:
            actuator_mock._api = self.api_mock

        self.tool_id = 1
        self.m3_output_mock = MagicMock()
        self.m4_output_mock = MagicMock()
        self.clockwise_tool_mock = {
            "uuid": self.m3_output_mock.configuration.uuid,
            "value": self.m3_output_mock.configuration.active_high,
        }
        self.counter_clockwise_tool_mock = {
            "uuid": self.m4_output_mock.configuration.uuid,
            "value": self.m4_output_mock.configuration.active_high,
        }
        self.controller_id_mock = self.actuator_x_mock.configuration.controller_id

    def test_given_path_follower_init_with_no_actuator_then_throws_exception(
        self,
    ) -> None:
        with self.assertRaises(PathFollowingException) as path_following_exception:
            PathFollower()
        self.assertEqual(
            "PathFollower object must contain at least one actuator",
            str(path_following_exception.exception),
        )

    def test_given_tool_id_and_m3_output_when_add_tool_then_calls_api_add_tool_with_tool_id_and_tool(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)
        tool_mock = {"cw": self.clockwise_tool_mock}

        # Act
        path_follower.add_tool(self.tool_id, self.m3_output_mock)
        # Assert
        self.add_path_tool_spy.assert_called_once_with(self.tool_id, tool_mock)

    def test_given_tool_id_and_outputs_when_add_tool_then_calls_api_add_tool_with_tool_id_and_tool(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)
        tool_mock = {
            "cw": self.clockwise_tool_mock,
            "ccw": self.counter_clockwise_tool_mock,
        }

        # Act
        path_follower.add_tool(self.tool_id, self.m3_output_mock, self.m4_output_mock)

        # Assert
        self.add_path_tool_spy.assert_called_once_with(self.tool_id, tool_mock)

    def test_given_gcode_when_start_path_then_calls_api_start_path_with_gcode_controller_id_and_wait_on_path_completion_true(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)
        gcode = MagicMock()
        wait_on_path_completion = True

        # Act
        path_follower.start_path(gcode)

        # Assert
        self.start_path_spy.assert_called_once_with(gcode, self.controller_id_mock, wait_on_path_completion)

    def test_given_gcode_when_start_path_async_then_calls_api_start_path_with_gcode_controller_id_and_wait_on_path_completion_false(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)
        gcode = MagicMock()
        wait_on_path_completion = False

        # Act
        path_follower.start_path_async(gcode)

        # Assert
        self.start_path_spy.assert_called_once_with(gcode, self.controller_id_mock, wait_on_path_completion)

    def test_when_stop_path_then_calls_api_stop_path_with_controller_id(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)

        # Act
        path_follower.stop_path()

        # Assert
        self.stop_path_spy.assert_called_once_with(self.controller_id_mock)

    def test_when_access_state_then_calls_api_get_path_status_with_gcode_controller_id(
        self,
    ) -> None:
        # Arrange
        path_follower = PathFollower(self.actuator_x_mock)

        # Act
        _ = path_follower.state.speed

        # Assert
        self.get_path_status_spy.assert_called_once_with(self.controller_id_mock)


if __name__ == "__main__":
    unittest.main()
