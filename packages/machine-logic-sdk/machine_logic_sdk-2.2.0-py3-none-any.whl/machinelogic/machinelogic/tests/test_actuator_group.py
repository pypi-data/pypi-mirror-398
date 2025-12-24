import unittest
from typing import Union
from unittest.mock import MagicMock

from machinelogic.ivention.exception import ActuatorGroupException
from machinelogic.ivention.types.batch_move import (
    ContinuousMove,
    TorqueMove,
    TrapezoidalMotion,
    TrapezoidalMove,
)
from machinelogic.machinelogic.actuator import Actuator
from machinelogic.machinelogic.actuator_group import ActuatorGroup


class TestActuatorGroup(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.config_mock_1 = MagicMock()
        self.config_mock_1.uuid = "actuator_uuid_1"
        self.config_mock_1.controller_id = "1234"
        self.config_mock_2 = MagicMock()
        self.config_mock_2.uuid = "actuator_uuid_2"
        self.config_mock_2.controller_id = "1234"

        self.actuator_1 = Actuator(self.config_mock_1, self.api_mock)
        self.actuator_2 = Actuator(self.config_mock_2, self.api_mock)

        self.actuator_group = ActuatorGroup(self.actuator_1, self.actuator_2)

    def test_move_absolute(self) -> None:
        # Arrange
        position = (100.0, 200.0)
        motion_profile = MagicMock()

        # Act
        self.actuator_group.move_absolute(position, motion_profile)

        # Assert
        self.api_mock.batch_move.assert_called_once()

    def test_move_relative(self) -> None:
        # Arrange
        distance = (50.0, 75.0)
        motion_profile = MagicMock()

        # Act
        self.actuator_group.move_relative(distance, motion_profile)

        # Assert
        self.api_mock.batch_move.assert_called_once()

    def test_move_absolute_async(self) -> None:
        # Arrange
        position = (100.0, 200.0)
        motion_profile = MagicMock()

        # Act
        self.actuator_group.move_absolute_async(position, motion_profile)

        # Assert
        self.api_mock.batch_move.assert_called_once()

    def test_move_relative_async(self) -> None:
        # Arrange
        distance = (50.0, 75.0)
        motion_profile = MagicMock()

        # Act
        self.actuator_group.move_relative_async(distance, motion_profile)

        # Assert
        self.api_mock.batch_move.assert_called_once()

    def test_wait_for_move_completion(self) -> None:
        # Arrange
        timeout = 10

        # Act
        self.actuator_group.wait_for_move_completion(timeout)

        # Assert
        self.api_mock.wait_for_motion_completion.assert_called_once()

    def test_stop(self) -> None:
        # Act
        self.actuator_group.stop()

        # Assert
        self.api_mock.stop_motion_combined.assert_called_once()

    def test_build_trapezoidal_motions(self) -> None:
        # Arrange
        positions = (100.0, 200.0)

        # Act
        motions = self.actuator_group._build_trapezoidal_motions(positions)

        # Assert
        self.assertEqual(len(motions), 2)
        self.assertEqual(motions[0].motor_address, "actuator_uuid_1")
        self.assertEqual(motions[0].position_target, 100.0)
        self.assertEqual(motions[1].motor_address, "actuator_uuid_2")
        self.assertEqual(motions[1].position_target, 200.0)

    def test_build_trapezoidal_motions_raises_exception_if_tuple_length_does_not_match_axes_length(
        self,
    ) -> None:
        # Arrange
        positions = (100.0, 200.0, 300.0)

        # Act & Assert
        with self.assertRaises(ActuatorGroupException):
            self.actuator_group._build_trapezoidal_motions(positions)

    def test_batch_move(self) -> None:
        # Arrange
        moves: list[Union[TrapezoidalMove, ContinuousMove, TorqueMove]] = [
            TrapezoidalMove(
                motions=[
                    TrapezoidalMotion(motor_address="actuator_uuid_1", position_target=100.0),
                    TrapezoidalMotion(motor_address="actuator_uuid_2", position_target=200.0),
                ],
                use_relative_reference=False,
                motion_profile=MagicMock(),
                ignore_synchronization=False,
            )
        ]
        error_message = "Unable to move"

        # Act
        self.actuator_group._batch_move(moves, error_message)

        # Assert
        self.api_mock.batch_move.assert_called_once()
        self.api_mock.get_axis_motion_completion.assert_called()

    def test_actuator_move_in_progress_is_updated_in_batch_move(self) -> None:
        # Arrange
        moves: list[Union[TrapezoidalMove, ContinuousMove, TorqueMove]] = [
            TrapezoidalMove(
                motions=[
                    TrapezoidalMotion(motor_address="actuator_uuid_1", position_target=100.0),
                    TrapezoidalMotion(motor_address="actuator_uuid_2", position_target=200.0),
                ],
                use_relative_reference=False,
                motion_profile=MagicMock(),
                ignore_synchronization=False,
            )
        ]
        error_message = "Unable to move"
        self.api_mock.get_axis_motion_completion.return_value = False

        # Act
        self.actuator_group._batch_move(moves, error_message)

        # Assert
        self.api_mock.get_axis_motion_completion.assert_called()
        self.assertTrue(self.actuator_1.state.move_in_progress)
        self.assertTrue(self.actuator_2.state.move_in_progress)

    def test_does_tuple_match_axes_length(self) -> None:
        # Arrange
        value = (100.0, 200.0)

        # Act
        result = self.actuator_group._does_tuple_match_axes_length(value)

        # Assert
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
