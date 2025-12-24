import unittest
from unittest.mock import MagicMock

from machinelogic.machinelogic.ac_motor import ACMotor


class TestACMotor(unittest.TestCase):
    def test_given_uuid_when_forward_move_then_calls_api_with_uuid(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.move_ac_motor = MagicMock()

        uuid = "ac_motor_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        ac_motor = ACMotor(config_mock, api_mock)

        # Act
        ac_motor.move_forward()

        # Assert
        api_mock.move_ac_motor.assert_called_once_with(uuid, "forward")

    def test_given_uuid_when_reverse_move_then_calls_api_with_uuid(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.move_ac_motor = MagicMock()

        uuid = "ac_motor_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        ac_motor = ACMotor(config_mock, api_mock)

        # Act
        ac_motor.move_reverse()

        # Assert
        api_mock.move_ac_motor.assert_called_once_with(uuid, "reverse")

    def test_given_uuid_when_stop_then_calls_api_with_uuid(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.stop_ac_motor = MagicMock()

        uuid = "ac_motor_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        ac_motor = ACMotor(config_mock, api_mock)

        # Act
        ac_motor.stop()

        # Assert
        api_mock.stop_ac_motor.assert_called_once_with(uuid)
