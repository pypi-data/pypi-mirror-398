import unittest
from unittest.mock import MagicMock

from ...ivention.exception import SceneException
from ...ivention.types.robot_calibration import RobotCalibration
from ...ivention.types.robot_types import CartesianPose
from ...machinelogic.calibration_frame import CalibrationFrame
from ...measurements.angle import UnitOfAngle
from ...measurements.distance import UnitOfDistance


class TestCalibrationFrame(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "1234"
        self.name = "test_frame"
        self.default_value = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ]
        self.calibration_frame = CalibrationFrame(self.uuid, self.name, self.default_value, self.api_mock)

        def create_robot_calibration(cartesian_pose: CartesianPose) -> RobotCalibration:
            return {
                "calibrated": {
                    "position": {
                        "x": {
                            "value": cartesian_pose[0],
                            "unit": UnitOfDistance.MILLIMETERS,
                        },
                        "y": {
                            "value": cartesian_pose[1],
                            "unit": UnitOfDistance.MILLIMETERS,
                        },
                        "z": {
                            "value": cartesian_pose[2],
                            "unit": UnitOfDistance.MILLIMETERS,
                        },
                    },
                    "rotation": {
                        "i": {"value": cartesian_pose[3], "unit": UnitOfAngle.DEGREE},
                        "j": {"value": cartesian_pose[4], "unit": UnitOfAngle.DEGREE},
                        "k": {"value": cartesian_pose[5], "unit": UnitOfAngle.DEGREE},
                    },
                },
            }

        self.create_robot_calibration = create_robot_calibration

    def test_get_default_value_from_initialized_calibration_frame_expect_to_return_default_value(
        self,
    ) -> None:
        self.assertEqual(self.calibration_frame.get_default_value(), self.default_value)

    def test_get_calibrated_value_given_robot_calibration_json_returns_proper_values_and_not_none(
        self,
    ) -> None:
        expected_calibrated_value = [1.0, 2.0, 3.0, 90.0, 90.0, 90.0]
        robot_calibration = self.create_robot_calibration(expected_calibrated_value)
        mock_robot_calibration_with_id = {"robotCalibration": {"id": self.uuid, **robot_calibration}}

        self.api_mock.get_calibration_frame.return_value = mock_robot_calibration_with_id

        calibrated_value = self.calibration_frame.get_calibrated_value()
        self.assertEqual(calibrated_value, expected_calibrated_value)
        self.api_mock.get_calibration_frame.assert_called_once_with(self.uuid)

    def test_set_calibrated_value_with_proper_values_expect_set_calibration_frame_to_be_called(
        self,
    ) -> None:
        new_frame = [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]
        self.calibration_frame.set_calibrated_value(new_frame)
        robot_calibration = self.create_robot_calibration(new_frame)
        self.api_mock.set_calibration_frame.assert_called_once_with(self.uuid, robot_calibration)

    def test_set_calibrated_value_raises_exception_if_api_request_returns_false(
        self,
    ) -> None:
        self.api_mock.set_calibration_frame.return_value = False

        new_frame = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        with self.assertRaises(SceneException):
            self.calibration_frame.set_calibrated_value(new_frame)


if __name__ == "__main__":
    unittest.main()
