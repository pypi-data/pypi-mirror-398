import unittest
from unittest.mock import MagicMock

from machinelogic.machinelogic.actuator import Actuator
from machinelogic.machinelogic.motion_profile import MotionProfile


class TestActuator(unittest.TestCase):
    def test_given_uuid_and_timeout_when_wait_for_move_completion_then_calls_api_with_uuid_and_timeout(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        wait_for_motion_completion_spy = MagicMock()
        api_mock.wait_for_motion_completion = wait_for_motion_completion_spy

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        timeout = 10
        actuator.wait_for_move_completion(timeout)

        # Assert
        wait_for_motion_completion_spy.assert_called_once_with(uuid, timeout=timeout)

    def test_given_uuid_and_distance_when_move_relative_then_calls_batch_move_with_correct_parameters(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        batch_move_spy = MagicMock()
        api_mock.batch_move = batch_move_spy

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        distance = 100
        motion_profile = MotionProfile(velocity=100, acceleration=100)
        actuator.move_relative(distance, motion_profile)

        # Assert
        batch_move_spy.assert_called_once()
        batch_move_call_args = batch_move_spy.call_args[0][0]
        self.assertEqual(batch_move_call_args.moves[0].motions[0].motor_address, uuid)
        self.assertEqual(batch_move_call_args.moves[0].motions[0].position_target, distance)
        self.assertTrue(batch_move_call_args.moves[0].use_relative_reference)
        self.assertEqual(
            batch_move_call_args.moves[0].motion_profile,
            motion_profile.strip_out_none_and_to_dict(),
        )

    def test_given_uuid_and_distance_when_move_relative_async_then_calls_batch_move_with_correct_parameters(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.batch_move = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        distance = 100
        motion_profile = MotionProfile(velocity=100, acceleration=100)
        actuator.move_relative_async(distance, motion_profile)

        # Assert
        api_mock.batch_move.assert_called_once()
        batch_move_call_args = api_mock.batch_move.call_args[0][0]
        self.assertEqual(batch_move_call_args.moves[0].motions[0].motor_address, uuid)
        self.assertEqual(batch_move_call_args.moves[0].motions[0].position_target, distance)
        self.assertTrue(batch_move_call_args.moves[0].use_relative_reference)
        self.assertEqual(
            batch_move_call_args.moves[0].motion_profile,
            motion_profile.strip_out_none_and_to_dict(),
        )

    def test_given_uuid_and_position_when_move_absolute_then_calls_batch_move_with_correct_parameters(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        batch_move_spy = MagicMock()
        api_mock.batch_move = batch_move_spy

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        position = 150
        motion_profile = MotionProfile(velocity=100, acceleration=100)
        actuator.move_absolute(position, motion_profile)

        # Assert
        batch_move_spy.assert_called_once()
        batch_move_call_args = batch_move_spy.call_args[0][0]
        self.assertEqual(batch_move_call_args.moves[0].motions[0].motor_address, uuid)
        self.assertEqual(batch_move_call_args.moves[0].motions[0].position_target, position)
        self.assertFalse(batch_move_call_args.moves[0].use_relative_reference)
        self.assertEqual(
            batch_move_call_args.moves[0].motion_profile,
            motion_profile.strip_out_none_and_to_dict(),
        )

    def test_given_uuid_and_position_when_move_absolute_async_then_calls_batch_move_with_correct_parameters(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.batch_move = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        position = 150
        motion_profile = MotionProfile(velocity=100, acceleration=100)
        actuator.move_absolute_async(position, motion_profile)

        # Assert
        api_mock.batch_move.assert_called_once()
        batch_move_call_args = api_mock.batch_move.call_args[0][0]
        self.assertEqual(batch_move_call_args.moves[0].motions[0].motor_address, uuid)
        self.assertEqual(batch_move_call_args.moves[0].motions[0].position_target, position)
        self.assertFalse(batch_move_call_args.moves[0].use_relative_reference)
        self.assertEqual(
            batch_move_call_args.moves[0].motion_profile,
            motion_profile.strip_out_none_and_to_dict(),
        )

    def test_given_uuid_and_motion_profile_when_move_continuous_async_then_calls_batch_move_with_correct_parameters(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.batch_move = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        motion_profile = MotionProfile(velocity=100, acceleration=100)
        actuator.move_continuous_async(motion_profile)

        # Assert
        api_mock.batch_move.assert_called_once()
        batch_move_call_args = api_mock.batch_move.call_args[0][0]
        self.assertEqual(batch_move_call_args.moves[0].motor_address, uuid)
        self.assertEqual(
            batch_move_call_args.moves[0].motion_profile,
            motion_profile.strip_out_none_and_to_dict(),
        )

    def test_given_uuid_and_timeout_when_home_then_calls_api_with_uuid_and_timeout(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.home = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        timeout = 10
        actuator.home(timeout)

        # Assert
        api_mock.home.assert_called_once_with(uuid, True, timeout)

    def test_given_uuid_when_stop_then_calls_api_with_uuid(
        self,
    ) -> None:
        # Arrange
        api_mock = MagicMock()
        api_mock.stop_motion = MagicMock()

        uuid = "actuator_uuid"
        config_mock = MagicMock()
        config_mock.uuid = uuid

        actuator = Actuator(config_mock, api_mock)

        # Act
        actuator.stop()

        # Assert
        api_mock.stop_motion.assert_called_once_with(uuid)


if __name__ == "__main__":
    unittest.main()
