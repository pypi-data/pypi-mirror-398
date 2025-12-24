import math
import unittest

from ...ivention.types.robot_pose import Pose
from ...machinelogic.utils.robot_pose_conversions import (
    convert_cartesian_pose_to_pose,
    convert_pose_to_cartesian_pose,
)
from ...measurements.angle import UnitOfAngle
from ...measurements.distance import UnitOfDistance


class TestPoseConversions(unittest.TestCase):
    def setUp(self) -> None:
        self.x_value = 1.0
        self.y_value = 2.0
        self.z_value = 3.0
        self.i_value = 10.0
        self.j_value = 20.0
        self.k_value = 30.0

        self.cartesian_pose = [
            self.x_value,
            self.y_value,
            self.z_value,
            self.i_value,
            self.j_value,
            self.k_value,
        ]

        self.pose: Pose = {
            "position": {
                "x": {"value": self.x_value, "unit": UnitOfDistance.MILLIMETERS},
                "y": {"value": self.y_value, "unit": UnitOfDistance.MILLIMETERS},
                "z": {"value": self.z_value, "unit": UnitOfDistance.MILLIMETERS},
            },
            "rotation": {
                "i": {"value": self.i_value, "unit": UnitOfAngle.DEGREE},
                "j": {"value": self.j_value, "unit": UnitOfAngle.DEGREE},
                "k": {"value": self.k_value, "unit": UnitOfAngle.DEGREE},
            },
        }

    def test_convert_pose_to_cartesian_pose_default_units(self) -> None:
        result = convert_pose_to_cartesian_pose(self.pose)

        for res, exp in zip(result, self.cartesian_pose):
            self.assertTrue(math.isclose(res, exp, rel_tol=1e-3))  # Using a relative tolerance

    def test_convert_cartesian_pose_to_pose(self) -> None:
        result = convert_cartesian_pose_to_pose(self.cartesian_pose)
        self.assertDictEqual(result, self.pose)


if __name__ == "__main__":
    unittest.main()
