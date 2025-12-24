import unittest
from typing import List, Union, cast
from unittest.mock import MagicMock

import numpy

from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.ireference_frame import IReferenceFrame
from machinelogic.machinelogic.cartesian_target import (
    CartesianTarget,
    CartesianTargetConfiguration,
)
from machinelogic.machinelogic.tests.MatrixAssertionsMixin import MatrixAssertionsMixin


class TestCartesianTargetConfiguration(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "cartesian-target-123"
        self.name = "test_cartesian_target"
        self.default_position = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.parent_reference_frame_id = "parent-ref-123"

        self.cartesian_target_config = CartesianTargetConfiguration(
            self.api_mock,
            self.uuid,
            self.name,
            self.default_position,
            self.parent_reference_frame_id,
        )

    def test_initialization_sets_properties_correctly(self) -> None:
        self.assertEqual(self.cartesian_target_config.uuid, self.uuid)
        self.assertEqual(self.cartesian_target_config.name, self.name)
        self.assertEqual(self.cartesian_target_config.default_position, self.default_position)
        self.assertEqual(self.cartesian_target_config._api, self.api_mock)

    def test_uuid_property_returns_expected_value(self) -> None:
        self.assertEqual(self.cartesian_target_config.uuid, self.uuid)

    def test_name_property_returns_expected_value(self) -> None:
        self.assertEqual(self.cartesian_target_config.name, self.name)

    def test_cartesian_pose_property_returns_expected_value(self) -> None:
        self.assertEqual(self.cartesian_target_config.default_position, self.default_position)


class TestCartesianTarget(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "cartesian-target-123"
        self.name = "test_cartesian_target"
        self.default_position = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.parent_reference_frame_id = "parent-ref-123"
        self.cartesian_target = CartesianTarget(
            self.uuid,
            self.name,
            self.default_position,
            self.api_mock,
            self.parent_reference_frame_id,
        )

    def test_initialization_creates_configuration_with_correct_values(self) -> None:
        self.assertIsInstance(self.cartesian_target._configuration, CartesianTargetConfiguration)
        self.assertEqual(self.cartesian_target._configuration.uuid, self.uuid)
        self.assertEqual(self.cartesian_target._configuration.name, self.name)
        self.assertEqual(self.cartesian_target._configuration.default_position, self.default_position)
        self.assertEqual(self.cartesian_target._configuration._api, self.api_mock)
        self.assertEqual(self.cartesian_target._api, self.api_mock)

    def test_get_cartesian_pose_returns_default_position_when_relative_to_is_parent(
        self,
    ) -> None:
        result = self.cartesian_target.get_position(relative_to="parent")
        self.assertEqual(result, self.default_position)

    def test_get_cartesian_pose_returns_default_position_when_relative_to_is_roobt_base(
        self,
    ) -> None:
        parent_calibration_frame_mock = MagicMock(spec=ICalibrationFrame)
        config_mock = MagicMock()
        config_mock.uuid = self.parent_reference_frame_id
        parent_calibration_frame_mock._configuration = config_mock
        parent_calibration_frame_mock.get_calibrated_value.return_value = None
        parent_calibration_frame_mock.get_default_value.return_value = [
            10,
            20,
            0,
            0,
            0,
            0,
        ]
        self.cartesian_target._assets = [
            parent_calibration_frame_mock,
        ]
        result = self.cartesian_target.get_position(relative_to="robot_base")
        self._assert_matrices_close(numpy.array(result), numpy.array([20.0, 40.0, 30.0, 40.0, 50.0, 60.0]))

    def test_get_cartesian_pose_reflects_configuration_changes(self) -> None:
        new_pose = [15.0, 25.0, 35.0, 45.0, 55.0, 65.0]
        self.cartesian_target._configuration._default_position = new_pose
        result = self.cartesian_target.get_position()
        self.assertEqual(result, new_pose)

    def test_set_asset_list_stores_assets(self) -> None:
        mock_assets: List[Union[IReferenceFrame, IJointTarget, ICalibrationFrame, ICartesianTarget]] = [
            cast(IReferenceFrame, MagicMock()),
            cast(IJointTarget, MagicMock()),
        ]
        self.cartesian_target._set_asset_list(mock_assets)
        self.assertEqual(self.cartesian_target._assets, mock_assets)


if __name__ == "__main__":
    unittest.main()
