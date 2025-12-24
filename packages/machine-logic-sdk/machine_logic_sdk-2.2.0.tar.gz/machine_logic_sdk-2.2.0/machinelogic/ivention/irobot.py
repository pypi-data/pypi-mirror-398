from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from enum import Enum
from typing import Callable, List, Union

from machinelogic.decorators.deprecated import deprecated, deprecated_property
from machinelogic.decorators.undocumented import undocumented
from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.ivention.types.robot_position_data import Timestamp
from machinelogic.ivention.types.robot_tcp import RobotTCP
from machinelogic.ivention.types.robot_types import (
    CartesianPose,
    DegreesPerSecond,
    DegreesPerSecondSquared,
    JointAnglesDegrees,
    Kilograms,
    MillimetersPerSecond,
    MillimetersPerSecondSquared,
)


class ISequenceBuilder(ABC):
    """
    Abstract class representing a sequence builder.
    """


TeachModeContextManager = AbstractContextManager


class IRobotAlarm(ABC):
    pass


class RobotOperationalState(Enum):
    """The robot's operational state."""

    # operational_state: NORMAL | FREEDRIVE | NON_OPERATIONAL | OFFLINE | UNKNOWN | NEED_MANUAL_INTERVENTION
    # uint8 STATE_OFFLINE=0
    # uint8 STATE_NON_OPERATIONAL=1
    # uint8 STATE_FREEDRIVE=2
    # uint8 STATE_NORMAL=3
    # uint8 STATE_UNKNOWN=4
    # uint8 STATE_NEED_MANUAL_INTERVENTION=5
    OFFLINE = 0
    NON_OPERATIONAL = 1
    FREEDRIVE = 2
    NORMAL = 3
    UNKNOWN = 4
    NEED_MANUAL_INTERVENTION = 5


class RobotSafetyState(Enum):
    """The robot's safety state."""

    # safety_state: NORMAL | ROBOT_EMERGENCY_STOP | REDUCED_SPEED | SAFEGUARD_STOP
    # uint8 SAFETY_NORMAL=0
    # uint8 SAFETY_EMERGENCY_STOP=2
    # uint8 SAFETY_REDUCED_SPEED=3
    # uint8 SAFETY_SAFEGUARD_STOP=4
    # uint8 SAFETY_STATE_UKNOWNN=5
    NORMAL = 0
    EMERGENCY_STOP = 2
    REDUCED_SPEED = 3
    SAFEGUARD_STOP = 4
    UNKNOWN = 5


class RobotConfiguration(ABC):
    """
    A representation of the configuration of a Robot instance.
    This configuration defines what your Robot is and how it
    should behave when work is requested from it.
    """

    def __init__(
        self,
        ros_address: str,
        uuid: str,
        name: str,
        robot_type: str,
        tcp_list: List[RobotTCP],
    ) -> None:
        self.__name = name
        self.__uuid = uuid
        self.__robot_type = robot_type
        self.__ros_address = ros_address
        self.__tcp_list = tcp_list
        self.__cartesian_velocity_limit: MillimetersPerSecond | None = None
        self.__joint_velocity_limit: DegreesPerSecond | None = None

    def __str__(self) -> str:
        """The string representation of the robot configuration."""
        return f"""{{
            Robot name: {self.name},
            uuid: {self.uuid},
            robot type: {self.robot_type},
            cartesian velocity limit: {self.cartesian_velocity_limit},
            joint velocity limit: {self.joint_velocity_limit}
            }}"""

    @property
    def name(self) -> str:
        """The friendly name of the robot."""
        return self.__name

    @property
    def uuid(self) -> str:
        """The robot's ID."""
        return self.__uuid

    @property
    def robot_type(self) -> str:
        """The robot's type."""
        return self.__robot_type

    @property
    def cartesian_velocity_limit(self) -> MillimetersPerSecond | None:
        """The maximum Cartesian velocity of the robot, in mm/s."""
        return self.__cartesian_velocity_limit

    @property
    def joint_velocity_limit(self) -> DegreesPerSecond | None:
        """The robot joints' maximum angular velocity, in deg/s."""
        return self.__joint_velocity_limit

    @property
    def tcp_list(self) -> List[RobotTCP]:
        """The list of available tool center points (TCPs) defined on the robot."""
        return self.__tcp_list

    @property
    @undocumented
    def _ros_address(self) -> str:
        """The address of the ROS-container or the robot."""
        return self.__ros_address

    @undocumented
    def _set_cartesian_velocity_limit(self, value: MillimetersPerSecond) -> None:
        self.__cartesian_velocity_limit = value

    @undocumented
    def _set_joint_velocity_limit(self, value: DegreesPerSecond) -> None:
        self.__joint_velocity_limit = value


class EulerSequence(Enum):
    """The valid Euler sequence orders."""

    ZYX = "ZYX"
    XYZ = "XYZ"
    ZYZ = "ZYZ"
    ZXZ = "ZXZ"
    YXY = "YXY"
    YZY = "YZY"
    XYX = "XYX"
    XZX = "XZX"


class IRobotState(ABC):
    """A representation of the robot current state."""

    @deprecated_property
    @abstractmethod
    def cartesian_position(self) -> CartesianPose:
        """(Deprecated) Use cartesian_position_data instead."""

    @deprecated_property
    @abstractmethod
    def joint_angles(self) -> JointAnglesDegrees:
        """(Deprecated) Use joint_angles_data instead."""

    @property
    @abstractmethod
    def cartesian_position_data(self) -> tuple[CartesianPose, Timestamp]:
        """
        A tuple of the robot current Cartesian position and the timestamp in seconds and milliseconds to epoch.
        """

    @property
    @abstractmethod
    def joint_angles_data(self) -> tuple[JointAnglesDegrees, Timestamp]:
        """
        A tuple of the robot current joint angles and the timestamp in seconds and milliseconds to epoch.
        """

    @property
    @abstractmethod
    def operational_state(self) -> RobotOperationalState:
        """The current robot operational state."""

    @property
    @abstractmethod
    def safety_state(self) -> RobotSafetyState:
        """The current robot safety state."""

    @property
    @abstractmethod
    def move_in_progress(self) -> bool:
        """Check if the robot is currently moving."""

    @property
    @abstractmethod
    def tcp_offset(self) -> CartesianPose:
        """The tool center point (TCP) offset, in mm and degrees, where the angles are extrinsic Euler angles in XYZ order."""

    @property
    @abstractmethod
    def active_tcp(self) -> Union[str, None]:
        """The name of the currently active tool center point (TCP)."""

    @abstractmethod
    def get_digital_input_value(self, pin: int) -> bool:
        """
        Returns the value of a digital input at a given pin.

        Args:
            pin (int): The pin number.

        Returns:
            True if the pin is high, False otherwise.
        """


class IRobot(ABC):
    """
    A software representation of a Robot. It is not recommended that you construct this
    object yourself. Rather, you should query it from a Machine instance:

    E.g.:
        machine = Machine()
        my_robot = machine.get_robot("Robot")

    In this example, "Robot" is the friendly name assigned to the actuator in the
    MachineLogic configuration page.
    """

    def __init__(self, configuration: RobotConfiguration) -> None:
        self._configuration = configuration

    @property
    @abstractmethod
    def state(self) -> IRobotState:
        """The current Robot state."""

    @property
    def configuration(self) -> RobotConfiguration:
        """The Robot configuration."""
        return self._configuration

    @abstractmethod
    def on_log_alarm(self, callback: Callable[[IRobotAlarm], None]) -> int:
        """
        Set a callback to the log alarm.

        Args:
            callback (Callable[[IRobotAlarm], None]): A callback function to be called when a robot alarm is received.

        Returns:
            int: The callback ID.
        """

    @abstractmethod
    def move_stop(self) -> bool:
        """
        Stops the robot current movement.

        Returns:
            bool: True if the robot was successfully stopped, False otherwise.
        """

    @abstractmethod
    def compute_forward_kinematics(self, joint_angles: JointAnglesDegrees) -> CartesianPose:
        """
        Computes the forward kinematics from joint angles.

        Args:
            joint_angles (JointAnglesDegrees): The 6 joint angles, in degrees.

        Returns:
            CartesianPose: Cartesian pose, in mm and degrees

        Raises:
            ValueError: Throws an error if the joint angles are invalid.
        """

    @abstractmethod
    def compute_inverse_kinematics(
        self,
        cartesian_position: CartesianPose,
        joint_constraints: list[IGenericJointConstraint] | None,
        seed_position: JointAnglesDegrees | None,
    ) -> JointAnglesDegrees:
        """
        Computes the inverse kinematics from a Cartesian pose.

        Args:
            cartesian_position (CartesianPose): The end effector's pose, in mm and degrees,
                where the angles are extrinsic Euler angles in XYZ order.
            joint_constraints (Optional[List[IGenericJointConstraint]], optional): A list of joint constraints. Length of list can be between 1 and number of joints on robot.
            seed_position (Optional[JointAnglesDegrees], optional): The seed joint angles, in degrees (as start position for IK search)

        Returns:
            JointAnglesDegrees: Joint angles, in degrees.

        Raises:
            ValueError: Throws an error if the inverse kinematic solver fails.
        """

    @deprecated
    @abstractmethod
    def set_tcp_offset(self, tcp_offset: CartesianPose) -> bool:
        """
        (Deprecated) This method is deprecated. Use set_active_tcp instead.
        Sets the tool center point offset.

        Args:
            tcp_offset (CartesianPose): The TCP offset, in mm and degrees, where the angles
                are extrinsic Euler angles in XYZ order.

        Returns:
            bool: True if the TCP offset was successfully set, False otherwise.
        """

    @abstractmethod
    def set_active_tcp(self, tcp_name: str) -> None:
        """
        Sets the active tool center point (TCP) by name.

        Args:
            tcp_name (str): The name of the TCP to set as active. Must be defined in the robot configuration.

        Raises:
            RobotException: If the TCP name does not exist in the robot configuration.
        """

    @abstractmethod
    def reset(self) -> bool:
        """
        Attempts to reset the robot to a normal operational state.

        Returns:
            bool: True if successful.
        """

    @undocumented
    @abstractmethod
    def set_tool_digital_output(self, pin: int, value: int) -> bool:
        """
        Sets the value of a tool digital output.

        Args:
            pin (int): The pin number.
            value (int): The value to set, where 1 is high and 0 is low.

        Returns:
            bool: True if successful.
        """

    @abstractmethod
    def set_payload(self, payload: Kilograms) -> bool:
        """
        Sets the payload of the robot.

        Args:
            payload (Kilograms): The payload, in kg.

        Returns:
            bool: True if successful.
        """

    @abstractmethod
    def create_sequence(self) -> ISequenceBuilder:
        """
        Creates a sequence-builder object for building a sequence of robot
        movements. This method is expected to be used with the `append_*`
        methods.

        Returns:
            SequenceBuilder: A sequence builder object.
        """

    @abstractmethod
    def on_system_state_change(self, callback: Callable[[RobotOperationalState, RobotSafetyState], None]) -> int:
        """
        Registers a callback for system state changes.

        Args:
            callback (Callable[[RobotOperationalState, RobotSafetyState], None]):
                The callback function.

        Returns:
            int: The callback ID.
        """

    @abstractmethod
    def movej(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        """
        Moves the robot to a specified joint position.

        Args:
            target (JointAnglesDegrees): The target joint angles, in degrees.
            velocity (DegreesPerSecond): The joint velocity to move at, in degrees per second.
            acceleration (DegreesPerSecondSquared): The joint acceleration to move at, in
                degrees per second squared.
        """

    @abstractmethod
    def movel(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: CartesianPose | None = None,
    ) -> None:
        """
        Moves the robot to a specified Cartesian position relative to the robot base,
        unless a specified reference frame is provided.

        Args:
            target (CartesianPose): The end effector's pose, in mm and degrees,
                where the angles are extrinsic Euler angles in XYZ order.
            velocity (MillimetersPerSecond): The velocity to move at, in mm/s.
            acceleration (MillimetersPerSecondSquared): The acceleration to move at, in mm/s^2.
            reference_frame (Optional[CartesianPose], optional): The reference frame to move relative to. If None,
                the robot's base frame is used.
        """

    @abstractmethod
    def movej_async(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        """
        Moves the robot to a specified joint position asynchronously.

        Args:
            target (JointAnglesDegrees): The target joint angles, in degrees.
            velocity (DegreesPerSecond): The joint velocity to move at, in degrees per second.
            acceleration (DegreesPerSecondSquared): The joint acceleration to move at, in
                degrees per second squared.
        """

    @abstractmethod
    def movel_async(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: CartesianPose | None = None,
    ) -> None:
        """
        Moves the robot to a specified Cartesian position asynchronously.

        Args:
            target (CartesianPose): The end effector's pose, in mm and degrees,
                where the angles are extrinsic Euler angles in XYZ order.
            velocity (MillimetersPerSecond): The velocity to move at, in mm/s.
            acceleration (MillimetersPerSecondSquared): The acceleration to move at, in mm/s^2.
            reference_frame (Optional[CartesianPose], optional): The reference frame to move relative to. If None,
                the robot's base frame is used.
        """

    @abstractmethod
    def execute_sequence(self, sequence: ISequenceBuilder) -> bool:
        """
        Moves the robot through a specific sequence of joint and linear motions.

        Args:
            sequence (SequenceBuilder): The sequence of target points.

        Returns:
            bool: True if successful.
        """

    @abstractmethod
    def execute_sequence_async(self, sequence: ISequenceBuilder) -> bool:
        """
        Moves the robot through a specific sequence of joint and linear motions asynchronously.

        Args:
            sequence (SequenceBuilder): The sequence of target points.

        Returns:
            bool: True if successful.
        """

    @abstractmethod
    def wait_for_motion_completion(self, timeout: float | None = None) -> bool:
        """
        Waits for the robot to complete its current motion. Used in asynchronous movements.

        Args:
            timeout (Optional[float], optional): The timeout in seconds, after which an exception will be thrown.

        Returns:
            bool: True if successful.

        Raises:
            RobotException: If the request fails or the move did not complete in
                the allocated amount of time.
        """

    @abstractmethod
    def reconnect(self, timeout: float | None = 15) -> bool:
        """
        It will disconnect then reconnect the MachineMotion to the robot.
        This is useful when operating the robot near its reach limits or other potential constraints
        where errors may cause the robot to disconnect automatically.
        It also facilitates re-connection while your application is still running.

        Args:
            timeout (Union[float, None]): The timeout in seconds, after which an exception will be thrown, default is 15 seconds.

        Returns:
            bool: True if successful.
        """

    @abstractmethod
    def teach_mode(
        self,
    ) -> TeachModeContextManager:  # type: ignore[type-arg]
        """
        Put the robot into teach mode (i.e., freedrive).

        Returns:
             TeachModeContextManager: A context manager that will exit teach mode when it is closed.
        """
