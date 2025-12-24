import unittest

from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint


class TestGenericJointConstraintPropertiesExist(unittest.TestCase):
    def test_joint_index_exists(self) -> None:
        self.assertTrue(hasattr(IGenericJointConstraint, "joint_index"))

    def test_position_exists(self) -> None:
        self.assertTrue(hasattr(IGenericJointConstraint, "position"))

    def test_tolerance_above_exists(self) -> None:
        self.assertTrue(hasattr(IGenericJointConstraint, "tolerance_above"))

    def test_tolerance_below_exists(self) -> None:
        self.assertTrue(hasattr(IGenericJointConstraint, "tolerance_below"))

    def test_weighting_factor_exists(self) -> None:
        self.assertTrue(hasattr(IGenericJointConstraint, "weighting_factor"))


if __name__ == "__main__":
    unittest.main()
