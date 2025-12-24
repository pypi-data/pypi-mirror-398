# mypy: disable-error-code="attr-defined, var-annotated, no-untyped-def"
import unittest
from typing import Callable, Optional
from unittest.mock import MagicMock

from machinelogic.decorators.deprecated import deprecated
from machinelogic.ivention.exception import MachineException
from machinelogic.ivention.iactuator import ActuatorConfiguration, IActuator
from machinelogic.ivention.icalibration_frame import ICalibrationFrame
from machinelogic.ivention.icartesian_target import ICartesianTarget
from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.ivention.ijoint_target import IJointTarget
from machinelogic.ivention.imachine import (
    IMachine,
    IMachineState,
    MachineOperationalState,
    MachineSafetyState,
)
from machinelogic.ivention.imachine_motion import IMachineMotion
from machinelogic.ivention.ireference_frame import IReferenceFrame
from machinelogic.ivention.irobot import (
    IRobot,
    IRobotAlarm,
    IRobotState,
    ISequenceBuilder,
    RobotConfiguration,
    RobotOperationalState,
    RobotSafetyState,
    TeachModeContextManager,
)
from machinelogic.ivention.iscene import IScene
from machinelogic.ivention.types.robot_types import (
    CartesianPose,
    DegreesPerSecond,
    DegreesPerSecondSquared,
    JointAnglesDegrees,
    Kilograms,
    MillimetersPerSecond,
    MillimetersPerSecondSquared,
)
from machinelogic.machinelogic.motion_profile import MotionProfile


class DummyRobotConfiguration(RobotConfiguration):
    @property
    def cartesian_velocity_limit(self) -> MillimetersPerSecond:
        raise NotImplementedError

    @property
    def joint_velocity_limit(self) -> DegreesPerSecond:
        raise NotImplementedError


class DummyMachineMotion(IMachineMotion):
    def __init__(
        self,
        actuators: Optional[list[IActuator]] = None,
        robots: Optional[list[IRobot]] = None,
    ):
        super().__init__(configuration=MagicMock())
        if actuators is not None:
            self._actuator_list.extend(actuators)  # pylint: disable=protected-access
        if robots is not None:
            self._robot_list.extend(robots)  # pylint: disable=protected-access


class DummyActuator(IActuator):
    def __init__(self, name: str, controller_id: str = "controller_id"):
        super().__init__(ActuatorConfiguration("uuid", name, "belt", "A", "mm", controller_id))

    def move_relative(
        self,
        distance: float,
        motion_profile: MotionProfile,
        ignore_end_sensor: bool = False,
        timeout: float = 0,
    ) -> None:
        raise NotImplementedError

    def move_relative_async(
        self,
        distance: float,
        motion_profile: MotionProfile,
        ignore_end_sensor: bool = False,
    ) -> None:
        raise NotImplementedError

    def move_absolute(
        self,
        position: float,
        motion_profile: MotionProfile,
        ignore_end_sensor: bool = False,
        timeout: float = 0,
    ) -> None:
        raise NotImplementedError

    def move_absolute_async(
        self,
        position: float,
        motion_profile: MotionProfile,
        ignore_end_sensor: bool = False,
    ) -> None:
        raise NotImplementedError

    def move_continuous_async(self, motion_profile: MotionProfile, ignore_end_sensor: bool = False) -> None:
        raise NotImplementedError

    def wait_for_move_completion(self, timeout: float = 300.0) -> None:
        raise NotImplementedError

    def home(self, timeout: float = 0) -> None:
        raise NotImplementedError

    def stop(self, acceleration: Optional[float] = None) -> None:
        raise NotImplementedError


class DummyRobot(IRobot):
    @property
    def state(self) -> IRobotState:
        raise NotImplementedError

    def on_log_alarm(self, callback: Callable[[IRobotAlarm], None]) -> int:
        raise NotImplementedError

    def move_stop(self) -> bool:
        raise NotImplementedError

    def compute_forward_kinematics(self, joint_angles: JointAnglesDegrees) -> CartesianPose:
        raise NotImplementedError

    def compute_inverse_kinematics(
        self,
        cartesian_position: CartesianPose,
        joint_constraints: Optional[list[IGenericJointConstraint]] = None,
        seed_position: Optional[JointAnglesDegrees] = None,
    ) -> JointAnglesDegrees:
        raise NotImplementedError

    @deprecated
    def set_tcp_offset(self, tcp_offset: CartesianPose) -> bool:
        raise NotImplementedError

    def set_active_tcp(self, tcp_name):
        raise NotImplementedError

    def reset(self) -> bool:
        raise NotImplementedError

    def set_tool_digital_output(self, pin: int, value: int) -> bool:
        raise NotImplementedError

    def create_sequence(self) -> ISequenceBuilder:
        raise NotImplementedError

    def set_payload(self, payload: Kilograms) -> bool:
        raise NotImplementedError

    def on_system_state_change(self, callback: Callable[[RobotOperationalState, RobotSafetyState], None]) -> int:
        raise NotImplementedError

    def movej(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        raise NotImplementedError

    def movel(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: Optional[CartesianPose] = None,
    ) -> None:
        raise NotImplementedError

    def movej_async(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        raise NotImplementedError

    def movel_async(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: Optional[CartesianPose] = None,
    ) -> None:
        raise NotImplementedError

    def wait_for_motion_completion(self, timeout: Optional[float] = None) -> bool:
        raise NotImplementedError

    def execute_sequence(self, sequence: ISequenceBuilder) -> bool:
        raise NotImplementedError

    def execute_sequence_async(self, sequence: ISequenceBuilder) -> bool:
        raise NotImplementedError

    def teach_mode(self) -> TeachModeContextManager:  # type: ignore[type-arg]
        raise NotImplementedError

    def reconnect(self, timeout: Optional[float] = None):
        raise NotImplementedError


class DummyScene(IScene):
    def get_calibration_frame(self, name: str) -> ICalibrationFrame:
        raise NotImplementedError

    def get_joint_target(self, name) -> IJointTarget:
        raise NotImplementedError

    def get_reference_frame(self, name: str) -> IReferenceFrame:
        raise NotImplementedError

    def get_cartesian_target(self, name: str) -> ICartesianTarget:
        raise NotImplementedError


class DummyMachine(IMachine):
    def on_system_state_change(self, callback: Callable[[MachineOperationalState, MachineSafetyState], None]) -> None:
        raise NotImplementedError

    def reset(self) -> bool:
        raise NotImplementedError

    @property
    def state(self) -> IMachineState:
        raise NotImplementedError


class TestIMachine(unittest.TestCase):
    def test_given_machine_motion_without_actuators_when_get_actuator_then_raises_machine_exception(
        self,
    ) -> None:
        # Arrange
        imachine = DummyMachine(
            machine_motions=[],
            mqtt_client=MagicMock(),
            scene=MagicMock(),
        )

        # Act & Assert
        actuator_name = "this actuator does not exist"
        with self.assertRaises(MachineException) as machine_exception:
            imachine.get_actuator(actuator_name)

        self.assertEqual(
            f"Unable to find actuator with name: {actuator_name}",
            str(machine_exception.exception),
        )

    def test_given_multiple_machine_motions_and_multiple_actuators_when_get_unknown_actuator_then_raises_machine_exception(
        self,
    ) -> None:
        # Arrange
        machine_motions: list[IMachineMotion] = [
            DummyMachineMotion(
                [
                    DummyActuator("actuator1"),
                    DummyActuator("actuator2"),
                ]
            ),
            DummyMachineMotion(
                [
                    DummyActuator("actuator3"),
                    DummyActuator("actuator4"),
                ]
            ),
        ]
        mqtt_client = MagicMock()
        scene = MagicMock()
        imachine = DummyMachine(machine_motions, mqtt_client, scene)

        # Act & Assert
        actuator_name = "this actuator does not exist"
        with self.assertRaises(MachineException) as machine_exception:
            imachine.get_actuator(actuator_name)

        self.assertEqual(
            f"Unable to find actuator with name: {actuator_name}",
            str(machine_exception.exception),
        )

    def test_given_multiple_machine_motions_and_multiple_actuators_when_get_actuator_then_finds_actuator(
        self,
    ) -> None:
        # Arrange
        actuators = [
            DummyActuator("actuator1"),
            DummyActuator("actuator2"),
            DummyActuator("actuator3"),
            DummyActuator("actuator4"),
        ]
        for expected_actuator in actuators:
            with self.subTest(actuator_name=expected_actuator.configuration.name):
                machine_motions: list[IMachineMotion] = [
                    DummyMachineMotion(
                        [
                            actuators[0],
                            actuators[1],
                        ]
                    ),
                    DummyMachineMotion(
                        [
                            actuators[2],
                            actuators[3],
                        ]
                    ),
                ]
                mqtt_client = MagicMock()
                scene = MagicMock()
                imachine = DummyMachine(machine_motions, mqtt_client, scene)

                # Act
                actual_actuator = imachine.get_actuator(expected_actuator.configuration.name)

                # Assert
                self.assertEqual(actual_actuator, expected_actuator)

    def test_given_multiple_machine_motions_and_multiple_actuators_with_the_same_names_when_get_actuator_then_finds_the_first_actuator_with_that_name(
        self,
    ) -> None:
        # Arrange
        expected_actuator = DummyActuator("actuator")
        machine_motions: list[IMachineMotion] = [
            DummyMachineMotion(
                [
                    expected_actuator,
                    DummyActuator("actuator"),
                ]
            ),
            DummyMachineMotion(
                [
                    DummyActuator("actuator"),
                    DummyActuator("actuator"),
                ]
            ),
        ]
        mqtt_client = MagicMock()
        scene = MagicMock()
        imachine = DummyMachine(machine_motions, mqtt_client, scene)

        # Act
        actual_actuator = imachine.get_actuator(expected_actuator.configuration.name)

        # Assert
        self.assertEqual(actual_actuator, expected_actuator)

    def test_given_machine_motion_and_robot_when_get_robot_finds_robot(self):
        # Arrange
        ros_address = "localhost://9091"
        uuid = "uuid"
        robot_1_type = "ur10_e"
        robot_1_name = "robot_1"
        robot_1_configuration = DummyRobotConfiguration(
            ros_address=ros_address,
            uuid=uuid,
            name=robot_1_name,
            robot_type=robot_1_type,
            tcp_list=[],
        )

        machine_motions: list[IMachineMotion] = [DummyMachineMotion(robots=[DummyRobot(robot_1_configuration)])]

        imachine = DummyMachine(
            machine_motions=machine_motions,
            mqtt_client=MagicMock(),
            scene=MagicMock(),
        )

        # Assert getting robot without name
        robot_found = imachine.get_robot()
        self.assertEqual(robot_found.configuration.name, robot_1_name)

        # Assert getting robot with correct name
        robot_found = imachine.get_robot(robot_1_name)
        self.assertEqual(robot_found.configuration.name, robot_1_name)

        # Assert getting exception when requesting wrong robot name
        with self.assertRaises(MachineException) as machine_exception:
            wrong_robot_name = "wrong robot name"
            imachine.get_robot(wrong_robot_name)

        self.assertEqual(
            f"Unable to find robot with name: {wrong_robot_name}",
            str(machine_exception.exception),
        )

    def test_given_machine_motion_without_robots_when_get_robot_then_raises_machine_exception(
        self,
    ) -> None:
        # Arrange
        imachine = DummyMachine(
            machine_motions=[],
            mqtt_client=MagicMock(),
            scene=MagicMock(),
        )

        # Act & Assert
        robot_name = "this robot does not exist"
        with self.assertRaises(MachineException) as machine_exception:
            imachine.get_robot(robot_name)

        self.assertEqual(
            "No robots found",
            str(machine_exception.exception),
        )

    def test_given_machine_with_scene(self) -> None:
        # Arrange
        scene_1 = DummyScene()

        imachine = DummyMachine(
            machine_motions=[],
            mqtt_client=MagicMock(),
            scene=scene_1,
        )

        # Assert getting robot with correct name
        scene_found = imachine.get_scene()
        self.assertEqual(scene_found, scene_1)

    def test_given_machine_with_no_scene(self) -> None:
        # Arrange

        imachine = DummyMachine(
            machine_motions=[],
            mqtt_client=MagicMock(),
            scene=None,  # type: ignore
        )

        with self.assertRaises(MachineException) as machine_exception:
            imachine.get_scene()

        self.assertEqual(
            "Unable to find scene associated with machine",
            str(machine_exception.exception),
        )


if __name__ == "__main__":
    unittest.main()
