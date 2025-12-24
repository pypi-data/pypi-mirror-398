import unittest
from typing import List, Union, cast
from unittest.mock import MagicMock

import numpy

from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.ireference_frame import (
    IReferenceFrame,
)
from machinelogic.machinelogic.reference_frame import (
    ReferenceFrame,
    ReferenceFrameConfiguration,
)
from machinelogic.machinelogic.tests.MatrixAssertionsMixin import MatrixAssertionsMixin


class TestReferenceFrameConfiguration(unittest.TestCase):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "ref-frame-123"
        self.name = "test_reference_frame"
        self.default_position = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.parent_reference_frame_id = "parent-ref-123"
        self.reference_frame_config = ReferenceFrameConfiguration(
            self.api_mock,
            self.uuid,
            self.name,
            self.default_position,
            self.parent_reference_frame_id,
        )

    def test_initialization_sets_properties_correctly(self) -> None:
        self.assertEqual(self.reference_frame_config.uuid, self.uuid)
        self.assertEqual(self.reference_frame_config.name, self.name)
        self.assertEqual(self.reference_frame_config.default_position, self.default_position)
        self.assertEqual(
            self.reference_frame_config.parent_reference_frame_id,
            self.parent_reference_frame_id,
        )
        self.assertEqual(self.reference_frame_config._api, self.api_mock)


class TestReferenceFrame(MatrixAssertionsMixin):
    def setUp(self) -> None:
        self.api_mock = MagicMock()
        self.uuid = "ref-frame-123"
        self.name = "test_reference_frame"
        self.default_position = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self.parent_reference_frame_id = "parent-ref-123"
        self.reference_frame = ReferenceFrame(
            self.uuid,
            self.name,
            self.default_position,
            self.api_mock,
            self.parent_reference_frame_id,
        )

    def test_initialization_creates_configuration_with_correct_values(self) -> None:
        self.assertIsInstance(self.reference_frame._configuration, ReferenceFrameConfiguration)
        self.assertEqual(self.reference_frame._configuration.uuid, self.uuid)
        self.assertEqual(self.reference_frame._configuration.name, self.name)
        self.assertEqual(self.reference_frame._configuration.default_position, self.default_position)
        self.assertEqual(
            self.reference_frame._configuration.parent_reference_frame_id,
            self.parent_reference_frame_id,
        )
        self.assertEqual(self.reference_frame._configuration._api, self.api_mock)
        self.assertEqual(self.reference_frame._api, self.api_mock)
        # Should start with an empty asset list
        self.assertEqual(self.reference_frame._assets, [])

    def test_get_position_returns_default_position_when_relative_to_is_parent(
        self,
    ) -> None:
        result = self.reference_frame.get_position(relative_to="parent")
        self.assertEqual(result, self.default_position)

    def test_get_position_returns_default_position_when_relative_to_is_robot_base(
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
        self.reference_frame._assets = [
            parent_calibration_frame_mock,
        ]

        result = self.reference_frame.get_position(relative_to="robot_base")

        self._assert_matrices_close(numpy.array(result), numpy.array([20.0, 40.0, 30.0, 40.0, 50.0, 60.0]))

    def test_get_position_default_parameter_is_robot_base(self) -> None:
        # Verify the default parameter works
        result = self.reference_frame.get_position()
        self.assertEqual(result, self.default_position)

    def test_set_asset_list_stores_assets(self) -> None:
        mock_assets: List[Union[IReferenceFrame, IJointTarget, ICalibrationFrame, ICartesianTarget]] = [
            cast(IReferenceFrame, MagicMock()),
            cast(IJointTarget, MagicMock()),
        ]
        self.reference_frame._set_asset_list(mock_assets)
        self.assertEqual(self.reference_frame._assets, mock_assets)


if __name__ == "__main__":
    unittest.main()
