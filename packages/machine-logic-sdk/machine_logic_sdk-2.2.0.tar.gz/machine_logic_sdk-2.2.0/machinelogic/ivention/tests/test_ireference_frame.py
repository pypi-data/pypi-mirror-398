import unittest

from machinelogic.ivention.ireference_frame import (
    IReferenceFrame,
    IReferenceFrameConfiguration,
)


class TestIReferenceFrameConfigurationMethodsExist(unittest.TestCase):
    def test_uuid_property_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrameConfiguration, "uuid"))

    def test_name_property_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrameConfiguration, "name"))

    def test_default_position_property_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrameConfiguration, "default_position"))

    def test_parent_reference_frame_id_property_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrameConfiguration, "parent_reference_frame_id"))


class TestIReferenceFrameMethodsExist(unittest.TestCase):
    def test_configuration_property_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrame, "_configuration"))

    def test_configuration_is_abstract(self) -> None:
        self.assertTrue("_configuration" in IReferenceFrame.__abstractmethods__)

    def test_get_position_exists(self) -> None:
        self.assertTrue(hasattr(IReferenceFrame, "get_position"))

    def test_get_position_is_abstract(self) -> None:
        self.assertTrue("get_position" in IReferenceFrame.__abstractmethods__)


if __name__ == "__main__":
    unittest.main()
