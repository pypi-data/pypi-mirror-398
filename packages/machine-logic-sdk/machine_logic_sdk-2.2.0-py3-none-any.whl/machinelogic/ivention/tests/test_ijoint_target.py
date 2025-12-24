import unittest

from machinelogic.ivention.ijoint_target import IJointTarget, IJointTargetConfiguration


class TestIJointTargetConfigurationMethodsExist(unittest.TestCase):
    def test_uuid_property_exists(self) -> None:
        self.assertTrue(hasattr(IJointTargetConfiguration, "uuid"))

    def test_name_property_exists(self) -> None:
        self.assertTrue(hasattr(IJointTargetConfiguration, "name"))

    def test_joint_angles_property_exists(self) -> None:
        self.assertTrue(hasattr(IJointTargetConfiguration, "joint_angles"))


class TestIJointTargetMethodsExist(unittest.TestCase):
    def test_get_joint_angles_exists(self) -> None:
        self.assertTrue(hasattr(IJointTarget, "get_joint_angles"))

    def test_get_joint_angles_is_abstract(self) -> None:
        self.assertTrue("get_joint_angles" in IJointTarget.__abstractmethods__)


if __name__ == "__main__":
    unittest.main()
