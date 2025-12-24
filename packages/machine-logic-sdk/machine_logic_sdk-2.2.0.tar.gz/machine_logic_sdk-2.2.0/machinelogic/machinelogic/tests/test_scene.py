import unittest
from typing import Any, List
from unittest.mock import MagicMock, patch

from machinelogic.ivention.exception import SceneException
from machinelogic.ivention.types.scene_assets import (
    AssetMapping,
    CalibrationFrameAsset,
    JointTargetAsset,
    ReferenceFrameAsset,
)
from machinelogic.machinelogic.api import Api
from machinelogic.machinelogic.calibration_frame import CalibrationFrame
from machinelogic.machinelogic.scene import Scene
from machinelogic.measurements.angle import UnitOfAngle
from machinelogic.measurements.distance import UnitOfDistance


class TestScene(unittest.TestCase):
    def setUp(self) -> None:
        # Create mock configurations and names

        def create_calibration_frame_json(name: str, cartesian_pose: List[float]) -> CalibrationFrameAsset:
            return {
                "id": "1234",
                "type": AssetMapping.CALIBRATION_FRAME,
                "parameters": {
                    "name": name,
                    "scope": "someScope",
                    "scopeId": "someScopeId",
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

        def create_joint_target_json(name: str, joint_angles: List[float]) -> JointTargetAsset:
            return {
                "id": "5678",
                "type": AssetMapping.JOINT_TARGET,
                "parameters": {
                    "name": name,
                    "scope": "someScope",
                    "scopeId": "someScopeId",
                    "jointAngles": [
                        {"value": joint_angles[0], "unit": UnitOfAngle.DEGREE},
                        {"value": joint_angles[1], "unit": UnitOfAngle.DEGREE},
                        {"value": joint_angles[2], "unit": UnitOfAngle.DEGREE},
                        {"value": joint_angles[3], "unit": UnitOfAngle.DEGREE},
                        {"value": joint_angles[4], "unit": UnitOfAngle.DEGREE},
                        {"value": joint_angles[5], "unit": UnitOfAngle.DEGREE},
                    ],
                },
            }

        def create_reference_frame_json(name: str, cartesian_pose: List[float], parent_id: str) -> ReferenceFrameAsset:
            return {
                "id": "9876",
                "type": AssetMapping.REFERENCE_FRAME,
                "parameters": {
                    "name": name,
                    "scope": "someScope",
                    "scopeId": "someScopeId",
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
                    "parentReferenceFrameId": parent_id,
                },
            }

        def create_cartesian_target_json(name: str, cartesian_pose: List[float], parent_id: str) -> ReferenceFrameAsset:
            return {
                "id": "4321",
                "type": AssetMapping.CARTESIAN_TARGET,
                "parameters": {
                    "name": name,
                    "scope": "someScope",
                    "scopeId": "someScopeId",
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
                    "parentReferenceFrameId": parent_id,
                },
            }

        self.create_calibration_frame_json = create_calibration_frame_json
        self.create_joint_target_json = create_joint_target_json
        self.create_reference_frame_json = create_reference_frame_json
        self.create_cartesian_target_json = create_cartesian_target_json

        mock_calibration_frame_configuration1 = MagicMock()
        mock_calibration_frame_configuration1.name = "frame1"
        mock_calibration_frame_configuration1.uuid = "uuid1"
        mock_calibration_frame_configuration1.default_value = [1, 1, 1, 1, 1, 1]

        mock_calibration_frame_configuration2 = MagicMock()
        mock_calibration_frame_configuration2.name = "frame2"
        mock_calibration_frame_configuration2.uuid = "uuid2"
        mock_calibration_frame_configuration2.default_value = [2, 2, 2, 2, 2, 2]

        # Create mock calibration frames and set their _configuration attributes
        self.mock_calibration_frame1 = MagicMock(spec=CalibrationFrame)
        self.mock_calibration_frame1._configuration = mock_calibration_frame_configuration1

        self.mock_calibration_frame2 = MagicMock(spec=CalibrationFrame)
        self.mock_calibration_frame2._configuration = mock_calibration_frame_configuration2

        self.api_mock = MagicMock(spec=Api)
        # Create a Scene
        self.scene = Scene(self.api_mock)

        self.get_scene_assets_spy = MagicMock()
        self.api_mock.get_scene_assets = self.get_scene_assets_spy

    def test_initialize_assets_with_calibration_frame(self) -> None:
        # Arrange
        calibration_frame_json = self.create_calibration_frame_json("frame1", [1, 1, 1, 90, 90, 90])
        scene_assets_json = {"assets": [calibration_frame_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        calibration_frame_parameters = calibration_frame_json["parameters"]
        expected_uuid = calibration_frame_json["id"]
        expected_name = calibration_frame_parameters["name"]
        position = calibration_frame_parameters["position"]
        rotation = calibration_frame_parameters["rotation"]
        expected_default_value = [
            position["x"]["value"],
            position["y"]["value"],
            position["z"]["value"],
            rotation["i"]["value"],
            rotation["j"]["value"],
            rotation["k"]["value"],
        ]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_calibration_frame = self.scene._calibration_frame_list[0]
        initialized_calibration_config = initialized_calibration_frame._configuration

        # Assert
        self.assertEqual(len(self.scene._calibration_frame_list), 1)
        self.assertEqual(initialized_calibration_config.uuid, expected_uuid)
        self.assertEqual(initialized_calibration_config.name, expected_name)
        self.assertEqual(initialized_calibration_config.default_value, expected_default_value)

    def test_initialize_assets_with_joint_target(self) -> None:
        # Arrange
        joint_target_json = self.create_joint_target_json("target1", [10, 20, 30, 40, 50, 60])
        scene_assets_json = {"assets": [joint_target_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        joint_target_parameters = joint_target_json["parameters"]
        expected_uuid = joint_target_json["id"]
        expected_name = joint_target_parameters["name"]
        joint_angles = joint_target_parameters["jointAngles"]
        expected_joint_angles = [joint_angle["value"] for joint_angle in joint_angles]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_joint_target = self.scene._joint_target_list[0]
        initialized_joint_target_config = initialized_joint_target._configuration

        # Assert
        self.assertEqual(len(self.scene._joint_target_list), 1)
        self.assertEqual(initialized_joint_target_config.uuid, expected_uuid)
        self.assertEqual(initialized_joint_target_config.name, expected_name)
        self.assertEqual(initialized_joint_target_config.joint_angles, expected_joint_angles)

    def test_initialize_assets_with_reference_frame(self) -> None:
        # Arrange
        reference_frame_json = self.create_reference_frame_json("ref_frame1", [10, 20, 30, 40, 50, 60], "parent_id_123")
        scene_assets_json = {"assets": [reference_frame_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        reference_frame_parameters = reference_frame_json["parameters"]
        expected_uuid = reference_frame_json["id"]
        expected_name = reference_frame_parameters["name"]
        expected_parent_id = reference_frame_parameters["parentReferenceFrameId"]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_reference_frame = self.scene._reference_frame_list[0]
        initialized_reference_config = initialized_reference_frame._configuration

        # Assert
        self.assertEqual(len(self.scene._reference_frame_list), 1)
        self.assertEqual(initialized_reference_config.uuid, expected_uuid)
        self.assertEqual(initialized_reference_config.name, expected_name)
        self.assertEqual(initialized_reference_config.parent_reference_frame_id, expected_parent_id)

    def test_initialize_assets_with_reference_frame_with_float_comparison(self) -> None:
        # Arrange
        reference_frame_json = self.create_reference_frame_json("ref_frame1", [10, 20, 30, 40, 50, 60], "parent_id_123")
        scene_assets_json = {"assets": [reference_frame_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        reference_frame_parameters = reference_frame_json["parameters"]
        expected_uuid = reference_frame_json["id"]
        expected_name = reference_frame_parameters["name"]
        expected_parent_id = reference_frame_parameters["parentReferenceFrameId"]
        position = reference_frame_parameters["position"]
        rotation = reference_frame_parameters["rotation"]
        expected_default_position = [
            position["x"]["value"],
            position["y"]["value"],
            position["z"]["value"],
            rotation["i"]["value"],
            rotation["j"]["value"],
            rotation["k"]["value"],
        ]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_reference_frame = self.scene._reference_frame_list[0]
        initialized_reference_config = initialized_reference_frame._configuration

        # Assert
        self.assertEqual(len(self.scene._reference_frame_list), 1)
        self.assertEqual(initialized_reference_config.uuid, expected_uuid)
        self.assertEqual(initialized_reference_config.name, expected_name)

        # Use assertAlmostEqual for each float value to handle floating point precision issues
        for i, (actual, expected) in enumerate(
            zip(
                initialized_reference_config.default_position,
                expected_default_position,
            )
        ):
            self.assertAlmostEqual(
                actual,
                expected,
                msg=f"Values at index {i} differ: {actual} != {expected}",
            )

        self.assertEqual(
            initialized_reference_config.parent_reference_frame_id,
            expected_parent_id,
        )

    def test_reference_frame_warning_with_multiple_matches(self) -> None:
        # Arrange
        mock_reference_frame = MagicMock()
        mock_config = MagicMock()
        mock_config.name = "ref_frame1"
        mock_config.uuid = "uuid1"
        mock_reference_frame._configuration = mock_config

        self.scene._reference_frame_list = [
            mock_reference_frame,
            mock_reference_frame,
        ]

        # Act & Assert
        with patch("machinelogic.machinelogic.scene.logging.warning") as mock_warning:
            result = self.scene.get_reference_frame("ref_frame1")
            self.assertEqual(result, mock_reference_frame)
            mock_warning.assert_called_once()

    def test_get_all_assets_returns_combined_list(self) -> None:
        # Arrange
        mock_calibration_frame = MagicMock()
        mock_joint_target = MagicMock()
        mock_reference_frame = MagicMock()

        self.scene._calibration_frame_list = [mock_calibration_frame]
        self.scene._joint_target_list = [mock_joint_target]
        self.scene._reference_frame_list = [mock_reference_frame]

        # Act
        result = self.scene._get_all_assets()

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIn(mock_calibration_frame, result)
        self.assertIn(mock_joint_target, result)
        self.assertIn(mock_reference_frame, result)

    def test_initialize_assets_with_mixed_asset_types(self) -> None:
        # Arrange
        calibration_frame_json = self.create_calibration_frame_json("frame1", [1, 2, 3, 4, 5, 6])
        joint_target_json = self.create_joint_target_json("target1", [10, 20, 30, 40, 50, 60])
        reference_frame_json = self.create_reference_frame_json("ref_frame1", [100, 200, 300, 400, 500, 600], "parent_id_123")

        scene_assets_json = {
            "assets": [
                calibration_frame_json,
                joint_target_json,
                reference_frame_json,
            ]
        }
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        # Act
        self.scene._initialize_assets(self.api_mock)

        # Assert
        self.assertEqual(len(self.scene._calibration_frame_list), 1)
        self.assertEqual(len(self.scene._joint_target_list), 1)
        self.assertEqual(len(self.scene._reference_frame_list), 1)

        # Check that _set_asset_list was called for the reference frame
        reference_frame = self.scene._reference_frame_list[0]
        self.assertEqual(len(reference_frame._assets), 3)
        self.assertEqual(
            {asset._configuration.name for asset in reference_frame._assets},
            {"frame1", "target1", "ref_frame1"},
        )

    def test_get_joint_target_where_joint_targets_exists(self) -> None:
        # Arrange
        mock_joint_target1 = MagicMock()
        mock_config1 = MagicMock()
        mock_config1.name = "target1"
        mock_joint_target1._configuration = mock_config1

        mock_joint_target2 = MagicMock()
        mock_config2 = MagicMock()
        mock_config2.name = "target2"
        mock_joint_target2._configuration = mock_config2

        self.scene._joint_target_list = [mock_joint_target1, mock_joint_target2]

        # Act & Assert
        result = self.scene.get_joint_target("target1")
        self.assertEqual(result, mock_joint_target1)

        result = self.scene.get_joint_target("target2")
        self.assertEqual(result, mock_joint_target2)

    def test_get_reference_frame_where_reference_frames_exists(self) -> None:
        # Arrange
        mock_reference_frame1 = MagicMock()
        mock_config1 = MagicMock()
        mock_config1.name = "ref_frame1"
        mock_reference_frame1._configuration = mock_config1

        mock_reference_frame2 = MagicMock()
        mock_config2 = MagicMock()
        mock_config2.name = "ref_frame2"
        mock_reference_frame2._configuration = mock_config2

        self.scene._reference_frame_list = [
            mock_reference_frame1,
            mock_reference_frame2,
        ]

        # Act & Assert
        result = self.scene.get_reference_frame("ref_frame1")
        self.assertEqual(result, mock_reference_frame1)

        result = self.scene.get_reference_frame("ref_frame2")
        self.assertEqual(result, mock_reference_frame2)

    @patch("machinelogic.machinelogic.scene.logging.warning")
    def test_get_calibration_frame_multiple_matches_expect_to_log_warning(self, mock_logger_warning: Any) -> None:
        # Arrange
        self.scene._calibration_frame_list = [
            self.mock_calibration_frame1,
            self.mock_calibration_frame1,
        ]

        # Act
        result = self.scene.get_calibration_frame("frame1")

        # Assert
        self.assertEqual(result, self.mock_calibration_frame1)
        mock_logger_warning.assert_called_once()

    def test_get_calibration_frame_where_calibration_frames_do_not_exists(self) -> None:
        # Test getting a calibration frame that does not exist
        with self.assertRaises(SceneException):
            self.scene.get_calibration_frame("nonexistent_frame")

    @patch("machinelogic.machinelogic.scene.logging.warning")
    def test_get_joint_target_multiple_matches_expect_to_log_warning(self, mock_logger_warning: Any) -> None:
        # Arrange
        mock_joint_target = MagicMock()
        mock_config = MagicMock()
        mock_config.name = "target1"
        mock_joint_target._configuration = mock_config

        self.scene._joint_target_list = [mock_joint_target, mock_joint_target]

        # Act
        result = self.scene.get_joint_target("target1")

        # Assert
        self.assertEqual(result, mock_joint_target)
        mock_logger_warning.assert_called_once()

    def test_get_joint_target_where_joint_targets_do_not_exist(self) -> None:
        # Test getting a joint target that does not exist
        with self.assertRaises(SceneException):
            self.scene.get_joint_target("nonexistent_target")

    def test_get_reference_frame_where_reference_frames_do_not_exist(self) -> None:
        # Test getting a reference frame that does not exist
        with self.assertRaises(SceneException):
            self.scene.get_reference_frame("nonexistent_ref_frame")

    def test_initialize_assets_with_cartesian_target(self) -> None:
        # Arrange
        cartesian_target_json = self.create_cartesian_target_json("cartesian_target1", [10, 20, 30, 40, 50, 60], "parent_id_123")
        scene_assets_json = {"assets": [cartesian_target_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        cartesian_target_parameters = cartesian_target_json["parameters"]
        expected_uuid = cartesian_target_json["id"]
        expected_name = cartesian_target_parameters["name"]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_cartesian_target = self.scene._cartesian_target_list[0]
        initialized_cartesian_target_config = initialized_cartesian_target._configuration

        # Assert
        self.assertEqual(len(self.scene._cartesian_target_list), 1)
        self.assertEqual(initialized_cartesian_target_config.uuid, expected_uuid)
        self.assertEqual(initialized_cartesian_target_config.name, expected_name)

    def test_initialize_assets_with_cartesian_target_with_float_comparison(
        self,
    ) -> None:
        # Arrange
        cartesian_target_json = self.create_cartesian_target_json("cartesian_target1", [10, 20, 30, 40, 50, 60], "parent_id_123")
        scene_assets_json = {"assets": [cartesian_target_json]}
        self.api_mock.get_scene_assets.return_value = scene_assets_json

        cartesian_target_parameters = cartesian_target_json["parameters"]
        position = cartesian_target_parameters["position"]
        rotation = cartesian_target_parameters["rotation"]
        expected_default_position = [
            position["x"]["value"],
            position["y"]["value"],
            position["z"]["value"],
            rotation["i"]["value"],
            rotation["j"]["value"],
            rotation["k"]["value"],
        ]

        # Act
        self.scene._initialize_assets(self.api_mock)
        initialized_cartesian_target = self.scene._cartesian_target_list[0]

        # Assert
        # Use assertAlmostEqual for each float value to handle floating point precision issues
        for i, (actual, expected) in enumerate(
            zip(
                initialized_cartesian_target.get_position(),
                expected_default_position,
            )
        ):
            self.assertAlmostEqual(
                actual,
                expected,
                msg=f"Values at index {i} differ: {actual} != {expected}",
            )

    def test_get_cartesian_target_where_cartesian_targets_exists(self) -> None:
        # Arrange
        mock_cartesian_target1 = MagicMock()
        mock_config1 = MagicMock()
        mock_config1.name = "cartesian_target1"
        mock_cartesian_target1._configuration = mock_config1

        mock_cartesian_target2 = MagicMock()
        mock_config2 = MagicMock()
        mock_config2.name = "cartesian_target2"
        mock_cartesian_target2._configuration = mock_config2

        self.scene._cartesian_target_list = [
            mock_cartesian_target1,
            mock_cartesian_target2,
        ]

        # Act & Assert
        result = self.scene.get_cartesian_target("cartesian_target1")
        self.assertEqual(result, mock_cartesian_target1)

        result = self.scene.get_cartesian_target("cartesian_target2")
        self.assertEqual(result, mock_cartesian_target2)

    @patch("machinelogic.machinelogic.scene.logging.warning")
    def test_get_cartesian_target_multiple_matches_expect_to_log_warning(self, mock_logger_warning: Any) -> None:
        # Arrange
        mock_cartesian_target = MagicMock()
        mock_config = MagicMock()
        mock_config.name = "cartesian_target1"
        mock_cartesian_target._configuration = mock_config

        self.scene._cartesian_target_list = [
            mock_cartesian_target,
            mock_cartesian_target,
        ]

        # Act
        result = self.scene.get_cartesian_target("cartesian_target1")

        # Assert
        self.assertEqual(result, mock_cartesian_target)
        mock_logger_warning.assert_called_once()

    def test_get_cartesian_target_where_cartesian_targets_do_not_exist(self) -> None:
        # Test getting a cartesian target that does not exist
        with self.assertRaises(SceneException):
            self.scene.get_cartesian_target("nonexistent_cartesian_target")

    def test_given_create_scene_calls_api_get_scene_assets(self) -> None:
        Scene(self.api_mock)
        self.get_scene_assets_spy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
