import unittest
from unittest.mock import MagicMock, patch

from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.machinelogic.robot.robot_utils import (
    DistanceUnit,
    Utils,
)
from machinelogic.machinelogic.robot.vention_ros_client_library import (
    RobotModel,
    RosRobotClient,
)


class TestRosRobotClient(unittest.TestCase):
    def setUp(self) -> None:
        self.mock_client = MagicMock()
        self.mock_container_manager = MagicMock()

        with patch.object(RosRobotClient, "_init_ros_client", return_value=None):
            self.robot_client = RosRobotClient(
                model=RobotModel.DOOSAN_H2017,
                pendant_ip="192.168.5.2",
                robot_controller_ip="192.168.137.100",
                port=9091,
                skip_container_management=True,
            )

        self.robot_client.client = self.mock_client
        self.robot_client.container_mananger = self.mock_container_manager
        self.robot_client._joint_velocity_limit = MagicMock()
        self.robot_client._joint_acceleration_limit = MagicMock()
        self.robot_client._cartesian_velocity_limit = MagicMock()
        self.robot_client._cartesian_acceleration_limit = MagicMock()

    @patch("machinelogic.machinelogic.robot.vention_ros_client_library.RosRobotClient._call_service")
    def test_inverse_kinematics_no_seed_no_joint_constraint(self, mock_call_service: MagicMock) -> None:
        # Arrange
        cartesian_position = [100.0, 200.0, 300.0, 0.0, 90.0, 0.0]
        expected_joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        mock_call_service.return_value = {"conv_posj": Utils.to_radians(expected_joint_angles)}

        # Act
        result = self.robot_client.inverse_kinematics(cartesian_position=cartesian_position)

        # Assert
        for result_joint, expected_joint in zip(result, expected_joint_angles):
            self.assertAlmostEqual(result_joint, expected_joint, delta=0.001)
        mock_call_service.assert_called_once_with(
            "vention_robots/compute_ik",
            "robot_commands_api/InverseKinematics",
            {
                "pos": Utils.to_meters(cartesian_position[:3], from_units=DistanceUnit.Millimeters)
                + Utils.to_quaternions(cartesian_position[3:]),
                "joint_seed_position": [],
                "joint_constraints": [],
                "sol_space": 0,
                "ref": 0,
            },
            timeout=180,
        )

    @patch("machinelogic.machinelogic.robot.vention_ros_client_library.RosRobotClient._call_service")
    def test_inverse_kinematics_with_seed(self, mock_call_service: MagicMock) -> None:
        # Arrange
        cartesian_position = [100.0, 200.0, 300.0, 0.0, 90.0, 0.0]
        seed_position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        expected_joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        mock_call_service.return_value = {"conv_posj": Utils.to_radians(expected_joint_angles)}

        # Act
        result = self.robot_client.inverse_kinematics(cartesian_position=cartesian_position, seed_position=seed_position)

        # Assert
        for result_joint, expected_joint in zip(result, expected_joint_angles):
            self.assertAlmostEqual(result_joint, expected_joint, delta=0.001)
        mock_call_service.assert_called_once_with(
            "vention_robots/compute_ik",
            "robot_commands_api/InverseKinematics",
            {
                "pos": Utils.to_meters(cartesian_position[:3], from_units=DistanceUnit.Millimeters)
                + Utils.to_quaternions(cartesian_position[3:]),
                "joint_seed_position": Utils.to_radians(seed_position),
                "joint_constraints": [],
                "sol_space": 0,
                "ref": 0,
            },
            timeout=180,
        )

    @patch("machinelogic.machinelogic.robot.vention_ros_client_library.RosRobotClient._call_service")
    def test_inverse_kinematics_with_joint_constraints(self, mock_call_service: MagicMock) -> None:
        # Arrange
        cartesian_position = [100.0, 200.0, 300.0, 0.0, 90.0, 0.0]
        position_1 = 10.0
        position_2 = 20.0
        tolerance_above = 5.0
        tolerance_below = 5.0
        weighting_factor = 1.0
        joint_constraints = [
            IGenericJointConstraint(
                joint_index=1,
                position=position_1,
                tolerance_above=tolerance_above,
                tolerance_below=tolerance_below,
                weighting_factor=weighting_factor,
            ),
            IGenericJointConstraint(
                joint_index=2,
                position=position_2,
                tolerance_above=tolerance_above,
                tolerance_below=tolerance_below,
                weighting_factor=weighting_factor,
            ),
        ]
        expected_joint_angles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        mock_call_service.return_value = {"conv_posj": Utils.to_radians(expected_joint_angles)}

        # Act
        result = self.robot_client.inverse_kinematics(cartesian_position=cartesian_position, joint_constraints=joint_constraints)

        # Assert
        for result_joint, expected_joint in zip(result, expected_joint_angles):
            self.assertAlmostEqual(result_joint, expected_joint, delta=0.001)
        mock_call_service.assert_called_once_with(
            "vention_robots/compute_ik",
            "robot_commands_api/InverseKinematics",
            {
                "pos": Utils.to_meters(cartesian_position[:3], from_units=DistanceUnit.Millimeters)
                + Utils.to_quaternions(cartesian_position[3:]),
                "joint_constraints": [
                    {
                        "joint_index": 0,
                        "position": Utils.to_radians([position_1])[0],
                        "tolerance_above": Utils.to_radians([tolerance_above])[0],
                        "tolerance_below": Utils.to_radians([tolerance_below])[0],
                        "weight": weighting_factor,
                    },
                    {
                        "joint_index": 1,
                        "position": Utils.to_radians([position_2])[0],
                        "tolerance_above": Utils.to_radians([tolerance_above])[0],
                        "tolerance_below": Utils.to_radians([tolerance_below])[0],
                        "weight": weighting_factor,
                    },
                ],
                "joint_seed_position": [],
                "sol_space": 0,
                "ref": 0,
            },
            timeout=180,
        )


if __name__ == "__main__":
    unittest.main()
