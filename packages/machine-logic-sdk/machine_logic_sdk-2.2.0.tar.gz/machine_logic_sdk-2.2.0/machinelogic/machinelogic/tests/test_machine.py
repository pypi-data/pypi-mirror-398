import unittest
from unittest.mock import MagicMock, patch

from machinelogic.ivention.imachine import MachineOperationalState, MachineSafetyState
from machinelogic.machinelogic.machine import Machine, MachineState


class TestMachine(unittest.TestCase):
    @patch("machinelogic.machinelogic.machine.Machine")
    def test_given_input_when_get_input_then_gets_correct_input(self, mock_machine: MagicMock) -> None:
        # Arrange
        machine = mock_machine.return_value
        machine_motion_mock = MagicMock()
        input_mock = MagicMock()
        config_mock = MagicMock()

        input_mock.configuration = config_mock
        input_mock.configuration.uuid = "uuid"

        machine.list_machine_motions.return_value = [machine_motion_mock]
        machine._get_input_by_uuid.return_value = input_mock

        # Act
        found_input = machine._get_input_by_uuid("uuid")

        # Assert
        self.assertEqual(found_input, input_mock)

    @patch("machinelogic.machinelogic.machine.Machine")
    def test_given_output_when_get_output_then_gets_correct_output(self, mock_machine: MagicMock) -> None:
        # Arrange
        machine = mock_machine.return_value
        machine_motion_mock = MagicMock()
        output_mock = MagicMock()
        config_mock = MagicMock()

        output_mock.configuration = config_mock
        output_mock.configuration.uuid = "uuid"

        machine.list_machine_motions.return_value = [machine_motion_mock]
        machine._get_output_by_uuid.return_value = output_mock

        # Act
        found_output = machine._get_output_by_uuid("uuid")

        # Assert
        self.assertEqual(found_output, output_mock)

    @patch("machinelogic.machinelogic.machine.Machine")
    def test_given_actuator_when_get_actuator_then_gets_correct_actuator(self, mock_machine: MagicMock) -> None:
        # Arrange
        machine = mock_machine.return_value
        machine_motion_mock = MagicMock()
        actuator_mock = MagicMock()
        config_mock = MagicMock()

        actuator_mock.configuration = config_mock
        actuator_mock.configuration.uuid = "uuid"

        machine.list_machine_motions.return_value = [machine_motion_mock]
        machine._get_actuator_by_uuid.return_value = actuator_mock

        # Act
        found_actuator = machine._get_actuator_by_uuid("uuid")

        # Assert
        self.assertEqual(found_actuator, actuator_mock)

    def test_machine_reset_calls_api_reset_controller_operational_state(self) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            api_mock = MagicMock()
            api_mock.reset_controller_operational_state = MagicMock()
            machine._api = api_mock

            # Act
            machine.reset()

            # Assert
            api_mock.reset_controller_operational_state.assert_called_once()

    def test_on_system_state_change_registers_callback(self) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            machine._on_state_change_callback = None
            machine.on_system_state_change(lambda x, y: None)
            # Act & Assert
            self.assertIsNotNone(machine._on_state_change_callback)

    def test_on_operational_state_update_exits_early_if_message_is_none(self) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            machine._on_state_change_callback = MagicMock()
            mock_topic = "machine-motion/operational-state"
            mock_message = None

            # Act
            machine._on_operational_state_update(mock_topic, mock_message)

            # Assert
            machine._on_state_change_callback.assert_not_called()

    def test_on_operational_state_update_calls_callback_with_correct_state(
        self,
    ) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            machine._on_state_change_callback = MagicMock()
            test_cases = [
                (
                    "machine-motion/operational-state",
                    "1",
                    MachineOperationalState.NORMAL,
                ),
                (
                    "machine-motion/operational-state",
                    "0",
                    MachineOperationalState.NON_OPERATIONAL,
                ),
            ]

            for topic, message, expected_operational_state in test_cases:
                machine._on_operational_state_update(topic, message)
                machine._on_state_change_callback.assert_called_once_with(expected_operational_state, machine._state.safety_state)
                machine._on_state_change_callback.reset_mock()

    def test_on_safety_state_update_exits_early_if_message_is_none(self) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            machine._on_state_change_callback = MagicMock()
            mock_topic = "machine-motion/safety-state"
            mock_message = None

            # Act
            machine._on_safety_state_update(mock_topic, mock_message)

            # Assert
            machine._on_state_change_callback.assert_not_called()

    def test_on_state_update(self) -> None:
        # Arrange
        with (
            patch("machinelogic.machinelogic.machine.Api", MagicMock()),
            patch("machinelogic.machinelogic.machine.MqttClient", MagicMock()),
            patch("machinelogic.machinelogic.machine.Scene", MagicMock()),
            patch("machinelogic.machinelogic.machine.MachineState", MagicMock()),
        ):
            machine = Machine()
            machine._on_state_change_callback = MagicMock()

            test_cases = [
                (
                    "machine-motion/safety-state",
                    "-1",
                    machine._state.operational_state,
                    MachineSafetyState.ERROR,
                ),
                (
                    "machine-motion/safety-state",
                    "0",
                    machine._state.operational_state,
                    MachineSafetyState.NONE,
                ),
                (
                    "machine-motion/safety-state",
                    "1",
                    machine._state.operational_state,
                    MachineSafetyState.EMERGENCY_STOP,
                ),
                (
                    "machine-motion/safety-state",
                    "2",
                    machine._state.operational_state,
                    MachineSafetyState.NORMAL,
                ),
            ]

            for (
                topic,
                message,
                expected_operational_state,
                expected_safety_state,
            ) in test_cases:
                machine._on_safety_state_update(topic, message)
                machine._on_state_change_callback.assert_called_once_with(expected_operational_state, expected_safety_state)
                machine._on_state_change_callback.reset_mock()

    def test_machine_state_getters_and_setters(self) -> None:
        # Arrange
        api_mock = MagicMock()
        machine_state = MachineState(api_mock)

        # Assert default values
        self.assertEqual(machine_state.safety_state, MachineSafetyState.NONE)
        self.assertEqual(machine_state.operational_state, MachineOperationalState.NON_OPERATIONAL)

        # Act
        machine_state.safety_state = MachineSafetyState.EMERGENCY_STOP
        machine_state.operational_state = MachineOperationalState.NORMAL

        # Assert
        self.assertEqual(machine_state.safety_state, MachineSafetyState.EMERGENCY_STOP)
        self.assertEqual(machine_state.operational_state, MachineOperationalState.NORMAL)


if __name__ == "__main__":
    unittest.main()
