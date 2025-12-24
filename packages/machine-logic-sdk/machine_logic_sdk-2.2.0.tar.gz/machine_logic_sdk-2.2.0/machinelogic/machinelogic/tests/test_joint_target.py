import unittest
from unittest.mock import MagicMock

from machinelogic.machinelogic.joint_target import JointTarget, JointTargetConfiguration


class TestJointTargetConfiguration(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "joint-target-123"
        self.name = "test_joint_target"
        self.joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.joint_target_config = JointTargetConfiguration(self.api_mock, self.uuid, self.name, self.joint_angles)

    def test_initialization_sets_properties_correctly(self) -> None:
        self.assertEqual(self.joint_target_config.uuid, self.uuid)
        self.assertEqual(self.joint_target_config.name, self.name)
        self.assertEqual(self.joint_target_config.joint_angles, self.joint_angles)
        self.assertEqual(self.joint_target_config._api, self.api_mock)

    def test_uuid_property_returns_expected_value(self) -> None:
        self.assertEqual(self.joint_target_config.uuid, self.uuid)

    def test_name_property_returns_expected_value(self) -> None:
        self.assertEqual(self.joint_target_config.name, self.name)

    def test_joint_angles_property_returns_expected_value(self) -> None:
        self.assertEqual(self.joint_target_config.joint_angles, self.joint_angles)


class TestJointTarget(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "joint-target-123"
        self.name = "test_joint_target"
        self.joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.joint_target = JointTarget(self.uuid, self.name, self.joint_angles, self.api_mock)

    def test_initialization_creates_configuration_with_correct_values(self) -> None:
        self.assertIsInstance(self.joint_target._configuration, JointTargetConfiguration)
        self.assertEqual(self.joint_target._configuration.uuid, self.uuid)
        self.assertEqual(self.joint_target._configuration.name, self.name)
        self.assertEqual(self.joint_target._configuration.joint_angles, self.joint_angles)
        self.assertEqual(self.joint_target._configuration._api, self.api_mock)
        self.assertEqual(self.joint_target._api, self.api_mock)

    def test_get_joint_angles_returns_configuration_joint_angles(self) -> None:
        result = self.joint_target.get_joint_angles()
        self.assertEqual(result, self.joint_angles)

    def test_get_joint_angles_reflects_configuration_changes(self) -> None:
        new_angles = [15.0, 25.0, 35.0, 45.0, 55.0, 65.0]
        self.joint_target._configuration._joint_angles = new_angles
        result = self.joint_target.get_joint_angles()
        self.assertEqual(result, new_angles)


if __name__ == "__main__":
    unittest.main()
