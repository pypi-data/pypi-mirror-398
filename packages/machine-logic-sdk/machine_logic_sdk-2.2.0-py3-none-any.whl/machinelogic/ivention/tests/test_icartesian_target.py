import unittest

from machinelogic.ivention.icartesian_target import (
    ICartesianTarget,
    ICartesianTargetConfiguration,
)


class TestICartesianTargetConfigurationMethodsExist(unittest.TestCase):
    def test_uuid_property_exists(self) -> None:
        self.assertTrue(hasattr(ICartesianTargetConfiguration, "uuid"))

    def test_name_property_exists(self) -> None:
        self.assertTrue(hasattr(ICartesianTargetConfiguration, "name"))

    def test_default_position_exists(self) -> None:
        self.assertTrue(hasattr(ICartesianTargetConfiguration, "default_position"))

    def test_parent_reference_frame_id_exists(self) -> None:
        self.assertTrue(hasattr(ICartesianTargetConfiguration, "parent_reference_frame_id"))


class TestICartesianTargetMethodsExist(unittest.TestCase):
    def test_get_position_exists(self) -> None:
        self.assertTrue(hasattr(ICartesianTarget, "get_position"))

    def test_get_position_is_abstract(self) -> None:
        self.assertTrue("get_position" in ICartesianTarget.__abstractmethods__)


if __name__ == "__main__":
    unittest.main()
