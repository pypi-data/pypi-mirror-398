import unittest
from unittest.mock import MagicMock

from machinelogic.ivention.machine_configuration import _parse_pneumatic_configuration
from machinelogic.machinelogic.pneumatic import Pneumatic


class TestPneumatic(unittest.TestCase):
    def test_given_uuid_when_pull_then_calls_api_with_uuid_and_wait_for_move_completion_false(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        mqtt_mock = MagicMock()
        api_mock.pneumatic_pull = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        pneumatic = Pneumatic(config_mock, api_mock, mqtt_mock)

        # Act
        pneumatic.pull_async()

        # Assert
        api_mock.pneumatic_pull.assert_called_once_with(uuid, False)

    def test_given_uuid_when_idle_then_calls_api_with_uuid(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        mqtt_mock = MagicMock()
        api_mock.pneumatic_idle = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid
        pneumatic = Pneumatic(config_mock, api_mock, mqtt_mock)

        # Act
        pneumatic.idle_async()

        # Assert
        api_mock.pneumatic_idle.assert_called_once_with(uuid)

    def test_pneumatic_state(self) -> None:
        api_mock = MagicMock()
        mqtt_mock = MagicMock()
        config_json = {
            "name": "Pneumatic 1",
            "uuid": "375b92d7-9660-463d-a3f8-047c84020966",
            "controllerId": "abc8f171-e023-4dfc-a08a-3db3e3e8b475",
            "ip": "localhost",
            "device": 1,
            "pushInPin": 2,
            "pullInPin": 3,
            "pushOutPin": 0,
            "pullOutPin": 1,
            "axisType": "pneumatic",
            "controlModuleAddress": {"devicePort": 1, "deviceId": 1},
        }
        config = _parse_pneumatic_configuration(config_json)
        pneumatic = Pneumatic(config, api_mock, mqtt_mock)

        pneumatic._update_pin_state([0, 0, 0, 0])
        self.assertEqual(pneumatic.state, "unknown")

        pneumatic._update_pin_state([0, 0, 1, 0])
        self.assertEqual(pneumatic.state, "pulled")

        pneumatic._update_pin_state([0, 0, 0, 1])
        self.assertEqual(pneumatic.state, "pushed")

        pneumatic._update_pin_state([0, 0, 1, 1])
        self.assertEqual(pneumatic.state, "transition")

    def test_given_uuid_when_push_then_calls_api_with_uuid_and_wait_for_move_completion_false(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        mqtt_mock = MagicMock()
        api_mock.pneumatic_push = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        pneumatic = Pneumatic(config_mock, api_mock, mqtt_mock)

        # Act
        pneumatic.push_async()

        # Assert
        api_mock.pneumatic_push.assert_called_once_with(uuid, False)


if __name__ == "__main__":
    unittest.main()
