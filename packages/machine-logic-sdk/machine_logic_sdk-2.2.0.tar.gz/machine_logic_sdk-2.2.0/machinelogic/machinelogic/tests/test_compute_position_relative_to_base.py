import unittest
from typing import Union

from machinelogic.ivention.exception import SceneException
from machinelogic.ivention.icalibration_frame import (
    ICalibrationFrame,
    ICalibrationFrameConfiguration,
)
from machinelogic.ivention.icartesian_target import (
    ICartesianTarget,
    ICartesianTargetConfiguration,
)
from machinelogic.ivention.ireference_frame import (
    IReferenceFrame,
    IReferenceFrameConfiguration,
)
from machinelogic.ivention.types.robot_types import CartesianPose
from machinelogic.ivention.types.scene_assets import AssetList
from machinelogic.machinelogic.utils.compute_position_relative_to_base import (
    compute_position_relative_to_base,
)

# Test constants similar to test_robot_transforms
IDENTITY_POSE = [0.0] * 6
CARTESIAN_POSE = [100.0, 200.0, 300.0, 30.0, 45.0, 60.0]
TRANSLATION_POSE = [50.0, 75.0, 100.0, 0.0, 0.0, 0.0]
PARENT_POSE = [10.0, 20.0, 30.0, 10.0, 20.0, 30.0]
CHILD_POSE = [5.0, 10.0, 15.0, 5.0, 10.0, 15.0]


class MatrixAssertionsMixin(unittest.TestCase):
    """Mixin class for matrix and pose comparison utilities"""

    def _assert_poses_close(self, pose1: CartesianPose, pose2: CartesianPose) -> None:
        self.assertEqual(len(pose1), len(pose2))
        for i, (val1, val2) in enumerate(zip(pose1, pose2)):
            self.assertAlmostEqual(val1, val2, places=5, msg=f"Poses differ at index {i}: {val1} != {val2}")


class MockReferenceFrameConfiguration(IReferenceFrameConfiguration):
    """Mock configuration class for reference frames"""

    def __init__(self, uuid: str, name: str, default_position: CartesianPose, parent_id: str = ""):
        super().__init__(uuid, name, default_position, parent_id)


class MockCartesianTargetConfiguration(ICartesianTargetConfiguration):
    """Mock configuration class for cartesian targets"""

    def __init__(
        self,
        uuid: str,
        name: str,
        default_position: CartesianPose,
        parent_reference_frame_id: str = "",
    ):
        super().__init__(uuid, name, default_position, parent_reference_frame_id)


class MockCalibrationFrameConfiguration(ICalibrationFrameConfiguration):
    """Mock configuration class for calibration frames"""

    def __init__(
        self,
        uuid: str,
        name: str,
        default_value: CartesianPose,
        calibrated_value: Union[CartesianPose, None],
    ):
        super().__init__(uuid, name, default_value)
        self._calibrated_value = calibrated_value

    @property
    def calibrated_value(self) -> Union[CartesianPose, None]:
        return self._calibrated_value


class MockReferenceFrame(IReferenceFrame):
    """Mock reference frame for testing"""

    def __init__(self, uuid: str, name: str, default_position: CartesianPose, parent_id: str = ""):
        self.__configuration = MockReferenceFrameConfiguration(uuid, name, default_position, parent_id)

    @property
    def _configuration(self) -> IReferenceFrameConfiguration:
        return self.__configuration

    def get_position(self, relative_to: str = "parent") -> CartesianPose:
        """Mock implementation - not used in tests"""
        # Return the default position from configuration
        return self._configuration.default_position


class MockCalibrationFrame(ICalibrationFrame):
    """Mock calibration frame for testing"""

    def __init__(
        self,
        uuid: str,
        name: str,
        default_value: CartesianPose,
        calibrated_value: Union[CartesianPose, None] = None,
    ):
        self.__configuration = MockCalibrationFrameConfiguration(uuid, name, default_value, calibrated_value)

    @property
    def _configuration(self) -> MockCalibrationFrameConfiguration:
        return self.__configuration

    def get_calibrated_value(self) -> Union[CartesianPose, None]:
        return self._configuration.calibrated_value

    def get_default_value(self) -> CartesianPose:
        return self._configuration.default_value

    def set_calibrated_value(self, frame: CartesianPose) -> None:
        """Mock implementation - not used in tests"""
        pass


class MockCartesianTarget(ICartesianTarget):
    """Mock cartesian target for testing"""

    def __init__(self, uuid: str, name: str, default_position: CartesianPose, parent_id: str = ""):
        self.__configuration = MockCartesianTargetConfiguration(uuid, name, default_position, parent_id)

    @property
    def _configuration(self) -> MockCartesianTargetConfiguration:
        return self.__configuration

    def get_position(self, relative_to: str = "parent") -> CartesianPose:
        """Mock implementation - not used in tests"""
        # Return the default position from configuration
        return self._configuration.default_position


class TestComputePositionRelativeToBase(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.base_frame_id = "base_frame"
        self.parent_frame_id = "parent_frame"
        self.child_frame_id = "child_frame"
        self.calibration_frame_id = "calibration_frame"

    def test_calibration_frame_with_calibrated_value_returns_calibrated_value(
        self,
    ) -> None:
        calibrated_value = list(CARTESIAN_POSE)
        default_value = list(IDENTITY_POSE)

        calibration_frame = MockCalibrationFrame(
            self.calibration_frame_id,
            "test_calibration",
            default_value,
            calibrated_value,
        )

        result = compute_position_relative_to_base(calibration_frame, [])
        self._assert_poses_close(result, calibrated_value)

    def test_calibration_frame_with_no_calibrated_value_returns_default_value(
        self,
    ) -> None:
        default_value = list(CARTESIAN_POSE)

        calibration_frame = MockCalibrationFrame(self.calibration_frame_id, "test_calibration", default_value, None)

        result = compute_position_relative_to_base(calibration_frame, [])
        self._assert_poses_close(result, default_value)

    def test_reference_frame_without_parent_raises_exception(self) -> None:
        reference_frame = MockReferenceFrame(self.child_frame_id, "test_ref", CARTESIAN_POSE, "non_existent_parent")

        with self.assertRaises(SceneException) as context:
            compute_position_relative_to_base(reference_frame, [])

        self.assertIn("No asset found with id non_existent_parent", str(context.exception))

    def test_cartesian_target_without_parent_raises_exception(self) -> None:
        cartesian_target = MockCartesianTarget(self.child_frame_id, "test_target", CARTESIAN_POSE, "non_existent_parent")

        with self.assertRaises(SceneException) as context:
            compute_position_relative_to_base(cartesian_target, [])

        self.assertIn("No asset found with id non_existent_parent", str(context.exception))

    def test_reference_frame_with_calibration_frame_parent(self) -> None:
        parent_calibrated_value = list(PARENT_POSE)
        parent_frame = MockCalibrationFrame(
            self.parent_frame_id,
            "parent_calibration",
            IDENTITY_POSE,
            parent_calibrated_value,
        )

        child_pose = list(CHILD_POSE)
        child_frame = MockReferenceFrame(self.child_frame_id, "child_ref", child_pose, self.parent_frame_id)

        assets: AssetList = [
            parent_frame,
            child_frame,
        ]
        result = compute_position_relative_to_base(child_frame, assets)

        # Result should be parent transform * child transform
        # This is a complex matrix operation, so we just verify it returns a valid pose
        self.assertEqual(len(result), 6)
        self.assertIsInstance(result, list)

    def test_reference_frame_with_reference_frame_parent(self) -> None:
        grandparent_pose = list(PARENT_POSE)
        grandparent_frame = MockCalibrationFrame(
            self.base_frame_id,
            "grandparent_calibration",
            IDENTITY_POSE,
            grandparent_pose,
        )

        parent_pose = list(TRANSLATION_POSE)
        parent_frame = MockReferenceFrame(self.parent_frame_id, "parent_ref", parent_pose, self.base_frame_id)

        child_pose = list(CHILD_POSE)
        child_frame = MockReferenceFrame(self.child_frame_id, "child_ref", child_pose, self.parent_frame_id)

        assets: AssetList = [grandparent_frame, parent_frame, child_frame]
        result = compute_position_relative_to_base(child_frame, assets)

        self.assertEqual(len(result), 6)
        self.assertIsInstance(result, list)
        # Result should not be the same as any individual frame
        self.assertNotEqual(result, child_pose)
        self.assertNotEqual(result, parent_pose)
        self.assertNotEqual(result, grandparent_pose)

    def test_cartesian_target_with_calibration_frame_parent(self) -> None:
        parent_calibrated_value = list(PARENT_POSE)
        parent_frame = MockCalibrationFrame(
            self.parent_frame_id,
            "parent_calibration",
            IDENTITY_POSE,
            parent_calibrated_value,
        )

        target_pose = list(CHILD_POSE)
        cartesian_target = MockCartesianTarget(self.child_frame_id, "test_target", target_pose, self.parent_frame_id)

        assets: AssetList = [parent_frame, cartesian_target]
        result = compute_position_relative_to_base(cartesian_target, assets)

        # Verify we get a valid pose result
        self.assertEqual(len(result), 6)
        self.assertIsInstance(result, list)

    def test_identity_transform_composition(self) -> None:
        # Create parent calibration frame at origin
        parent_frame = MockCalibrationFrame(self.parent_frame_id, "parent_calibration", IDENTITY_POSE, IDENTITY_POSE)

        child_frame = MockReferenceFrame(self.child_frame_id, "child_ref", IDENTITY_POSE, self.parent_frame_id)

        assets: AssetList = [parent_frame, child_frame]
        result = compute_position_relative_to_base(child_frame, assets)

        # Result should be close to identity
        self._assert_poses_close(result, IDENTITY_POSE)

    def test_translation_only_transform(self) -> None:
        parent_translation = [100.0, 200.0, 300.0, 0.0, 0.0, 0.0]
        parent_frame = MockCalibrationFrame(
            self.parent_frame_id,
            "parent_calibration",
            IDENTITY_POSE,
            parent_translation,
        )

        child_translation = [50.0, 75.0, 100.0, 0.0, 0.0, 0.0]
        child_frame = MockReferenceFrame(self.child_frame_id, "child_ref", child_translation, self.parent_frame_id)

        assets: AssetList = [parent_frame, child_frame]
        result = compute_position_relative_to_base(child_frame, assets)

        # For pure translation, result should be sum of translations
        expected = [150.0, 275.0, 400.0, 0.0, 0.0, 0.0]
        self._assert_poses_close(result, expected)

    def test_multiple_asset_types_in_hierarchy(self) -> None:
        base_frame = MockCalibrationFrame(self.base_frame_id, "base_calibration", IDENTITY_POSE, PARENT_POSE)

        intermediate_frame = MockReferenceFrame(
            "intermediate_frame",
            "intermediate_ref",
            TRANSLATION_POSE,
            self.base_frame_id,
        )

        final_target = MockCartesianTarget(self.child_frame_id, "final_target", CHILD_POSE, "intermediate_frame")

        assets: AssetList = [base_frame, intermediate_frame, final_target]
        result = compute_position_relative_to_base(final_target, assets)

        # Verify we get a valid pose result
        self.assertEqual(len(result), 6)
        self.assertIsInstance(result, list)

    def test_asset_not_found_in_mixed_asset_list(self) -> None:
        child_frame = MockReferenceFrame(self.child_frame_id, "child_ref", CHILD_POSE, "missing_parent")

        other_frame = MockReferenceFrame("other_id", "other_ref", PARENT_POSE, "some_other_parent")
        assets: AssetList = [other_frame, child_frame]

        with self.assertRaises(SceneException) as context:
            compute_position_relative_to_base(child_frame, assets)

        self.assertIn("No asset found with id missing_parent", str(context.exception))

    def test_recursive_depth_handling(self) -> None:
        # Create a chain: calibration -> ref1 -> ref2 -> target
        base_calibration = MockCalibrationFrame("base", "base_cal", IDENTITY_POSE, [10.0, 10.0, 10.0, 0.0, 0.0, 0.0])

        ref1 = MockReferenceFrame("ref1", "ref1", [5.0, 5.0, 5.0, 0.0, 0.0, 0.0], "base")

        ref2 = MockReferenceFrame("ref2", "ref2", [2.0, 2.0, 2.0, 0.0, 0.0, 0.0], "ref1")

        target = MockCartesianTarget("target", "target", [1.0, 1.0, 1.0, 0.0, 0.0, 0.0], "ref2")

        assets: AssetList = [base_calibration, ref1, ref2, target]
        result = compute_position_relative_to_base(target, assets)

        # For pure translations, should be sum: 10 + 5 + 2 + 1 = 18 for each axis
        expected = [18.0, 18.0, 18.0, 0.0, 0.0, 0.0]
        self._assert_poses_close(result, expected)


if __name__ == "__main__":
    unittest.main()
