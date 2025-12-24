from __future__ import annotations

import math
from collections import namedtuple
from typing import Callable, Union
from urllib.parse import urlparse

from machinelogic.decorators.deprecated import deprecated, deprecated_property
from machinelogic.ivention.exception import RobotException
from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.ivention.irobot import (
    IRobot,
    IRobotState,
    ISequenceBuilder,
    RobotConfiguration,
    RobotOperationalState,
    RobotSafetyState,
)
from machinelogic.ivention.types.robot_position_data import Timestamp
from machinelogic.ivention.types.robot_types import (
    CartesianPose,
    DegreesPerSecond,
    DegreesPerSecondSquared,
    JointAnglesDegrees,
    Kilograms,
    MillimetersPerSecond,
    MillimetersPerSecondSquared,
)
from machinelogic.ivention.util.inheritance import inherit_docstrings  # type: ignore
from machinelogic.machinelogic.robot.robot_utils import (
    DistanceUnit,
    Utils,
)

from ..api import Api
from .vention_ros_client_library import RobotAlarm, RosRobotClient

# Address used to connect to the robot in the Vention-ROS container.
RosAddress = namedtuple("RosAddress", ["host", "port"])


def round_array_elements(array: list[float], num_digits: int = 2) -> list[float]:
    """
    Round array elements to a given number of digits.

    Args:
        array (List[float]): The array to round.
        num_digits (int): The number of digits to round to.
    """
    return [round(element, num_digits) for element in array]


def parse_ros_address(ros_url: str) -> RosAddress:
    """
    Parses the ROS URL into a host and a port that can be used to connect to the robot.

    Args:
        ros_url: The ROS raw URL.
    """
    parsed_url = urlparse(ros_url)

    port: int | None = parsed_url.port
    host: str = str(parsed_url.hostname)

    # If not running on remote/demo, then the constructor is done
    if parsed_url.scheme != "wss":
        return RosAddress(host=host, port=port)

    # If running on remote/demo, then append the port to the hostname.
    # Using 'wss' scheme with a port is not supported by the ROS Python library (roslibpy).
    port = None
    port_str = parsed_url.path.split("/")[-1]
    if port_str.isnumeric():
        host = f"{ros_url}:{port_str}"

    return RosAddress(host=host, port=port)


def log_alarm_callback(
    log_alarm: RobotAlarm,
    exception_alarm_level: RobotAlarm.Level | None = RobotAlarm.Level.ERROR,
    print_alarm_level: RobotAlarm.Level | None = RobotAlarm.Level.INFO,
) -> None:
    """
    A robot alarm callback function that logs the alarms to the Programmatic
    interface.

    Args:
        log_alarm: The alarm value and message.
        exception_alarm_level: The level at which to raise an exception. If set to None, then doesn't raise an exception.
        print_alarm_level: The level at which to print the alarm, without an exception. If set to None, then doesn't print the alarm info.
    """

    def should_trigger_alarm(alarm_level: RobotAlarm.Level, trigger_level: RobotAlarm.Level | None) -> bool:
        if trigger_level is None:
            return False
        if trigger_level is RobotAlarm.Level.ERROR:
            return alarm_level is RobotAlarm.Level.ERROR
        if trigger_level is RobotAlarm.Level.WARNING:
            return alarm_level in (RobotAlarm.Level.ERROR, RobotAlarm.Level.WARNING)
        return True

    if should_trigger_alarm(log_alarm.level, exception_alarm_level):
        raise RobotException(f"[{log_alarm.level.value}]: " + log_alarm.description)

    if should_trigger_alarm(log_alarm.level, print_alarm_level):
        print(f"[{log_alarm.level.value}]: " + log_alarm.description)


class RosRobotSingleton:
    """A singleton class to hold a connection to the ROS robot."""

    __instance: RosRobotClient | None = None

    @staticmethod
    def get_instance(
        ros_address: str,
        ip_address_override: str | None = None,
        exception_alarm_level: RobotAlarm.Level | None = RobotAlarm.Level.ERROR,
        print_alarm_level: RobotAlarm.Level | None = RobotAlarm.Level.WARNING,
    ) -> RosRobotClient:
        """
        Gets an instance of the ROS robot.

        Args:
            ros_address: The ROS raw URL.
            exception_alarm_level: The level at which to raise an exception.
            print_alarm_level: The level at which to print the alarm.

        Returns:
            The connected ROS robot.
        """
        if RosRobotSingleton.__instance is None:
            parsed_ros_address = parse_ros_address(ros_address)
            RosRobotSingleton.__instance = RosRobotClient(
                pendant_ip=ip_address_override if ip_address_override is not None else parsed_ros_address.host,
                port=parsed_ros_address.port,
                skip_container_management=True,
                on_log_alarm=lambda log_alarm: log_alarm_callback(
                    log_alarm,
                    exception_alarm_level=exception_alarm_level,
                    print_alarm_level=print_alarm_level,
                ),
            )
        return RosRobotSingleton.__instance


@inherit_docstrings
class RobotState(IRobotState):
    def __init__(self, ros_robot: RosRobotClient, api: Api, configuration: RobotConfiguration):
        self._ros_robot: RosRobotClient = ros_robot
        self._api = api
        self._configuration = configuration

    @deprecated_property
    def cartesian_position(self) -> CartesianPose:
        pose, _ = self._ros_robot.get_cartesian_position()
        return round_array_elements(pose)

    @deprecated_property
    def joint_angles(self) -> JointAnglesDegrees:
        pose, _ = self._ros_robot.get_joint_positions()
        return round_array_elements(pose)

    @property
    def cartesian_position_data(self) -> tuple[CartesianPose, Timestamp]:
        pose, timestamp = self._ros_robot.get_cartesian_position()
        return round_array_elements(pose), timestamp

    @property
    def joint_angles_data(self) -> tuple[JointAnglesDegrees, Timestamp]:
        pose, timestamp = self._ros_robot.get_joint_positions()
        return round_array_elements(pose), timestamp

    @property
    def operational_state(self) -> RobotOperationalState:
        return self._ros_robot.get_robot_state()

    @property
    def safety_state(self) -> RobotSafetyState:
        return self._ros_robot.get_safety_state()

    @property
    def move_in_progress(self) -> bool:
        return self._ros_robot.get_move_in_progress()

    @property
    def tcp_offset(self) -> CartesianPose:
        # we have to query the api to get the active because it may have been changed
        # outside of the context of this sdk
        active_tcp = self._api.get_active_tcp(self._configuration.uuid)

        offsetList = [
            active_tcp["offset"]["x"],
            active_tcp["offset"]["y"],
            active_tcp["offset"]["z"],
            active_tcp["offset"]["i"],
            active_tcp["offset"]["j"],
            active_tcp["offset"]["k"],
        ]
        offset_position_mm = Utils.to_millimeters(offsetList[:3], from_units=DistanceUnit.Meters)
        offset_rotation_degrees = Utils.to_degrees(offsetList[3:])
        return offset_position_mm + offset_rotation_degrees

    @property
    def active_tcp(self) -> Union[str, None]:
        # we have to query the api to get the active because it may have been changed
        # outside of the context of this sdk
        active_tcp = self._api.get_active_tcp(self._configuration.uuid)
        for tcp_item in self._configuration.tcp_list:
            if tcp_item.uuid == active_tcp["tcpUuid"]:
                return tcp_item.name
        return None

    def get_digital_input_value(self, pin: int) -> bool:
        return bool(self._ros_robot.get_tool_digital_input(pin))


@inherit_docstrings
class Robot(IRobot):
    """A representation of a Vention Robot."""

    def __init__(self, configuration: RobotConfiguration, api: Api, ip_address: str | None = None):
        super().__init__(configuration)
        self._configuration = configuration
        self._robot: RosRobotClient = RosRobotSingleton.get_instance(
            ros_address=configuration._ros_address,
            ip_address_override=ip_address,
        )
        self._api = api

        self._state = RobotState(self._robot, self._api, self._configuration)

        configuration._set_cartesian_velocity_limit(self._robot.get_cartesian_velocity_limit())
        configuration._set_joint_velocity_limit(self._robot.get_joint_velocity_limit())

    @property
    def state(self) -> RobotState:
        return self._state

    def on_log_alarm(self, callback: Callable[[RobotAlarm], None]) -> int:
        return int(self._robot.on_log_alarm(callback))

    def move_stop(self) -> bool:
        return bool(self._robot.move_stop())

    def compute_forward_kinematics(self, joint_angles: JointAnglesDegrees) -> CartesianPose:
        if len(joint_angles) != 6:
            raise ValueError("Joint angles must be a list of 6 joint angles, in degrees.")
        pose = self._robot.forward_kinematics(joint_angles)
        return round_array_elements(pose)

    def compute_inverse_kinematics(
        self,
        cartesian_position: CartesianPose,
        joint_constraints: list[IGenericJointConstraint] | None = None,
        seed_position: JointAnglesDegrees | None = None,
    ) -> JointAnglesDegrees:
        joint_angles = self._robot.inverse_kinematics(cartesian_position, joint_constraints, seed_position=seed_position)
        return round_array_elements(joint_angles)

    @deprecated
    def set_tcp_offset(self, tcp_offset: CartesianPose) -> bool:
        def to_radians(degrees: list[float]) -> list[float]:
            return [math.radians(angle) for angle in degrees]

        def to_meters(millimeters: list[float]) -> list[float]:
            return [distance / 1000 for distance in millimeters]

        rad = to_radians(tcp_offset[3:])
        meters = to_meters(tcp_offset[:3])

        tcp_offset_payload = [0.0] * 6
        tcp_offset_payload[:3] = meters
        tcp_offset_payload[3:] = rad

        response = self._api.set_tcp_offset(self._configuration.uuid, tcp_offset_payload)
        return response

    def set_active_tcp(self, tcp_name: str) -> None:
        tcp_uuid = None
        for tcp in self._configuration.tcp_list:
            if tcp.name == tcp_name:
                tcp_uuid = tcp.uuid
                break

        if tcp_uuid is None:
            raise RobotException(f"TCP with name {tcp_name} not found")

        if not self._api.set_active_tcp(self._configuration.uuid, tcp_uuid):
            raise RobotException(f"Failed to set active TCP to {tcp_name}")

    def reset(self) -> bool:
        response = self._robot.reset()
        return bool(response["success"])

    def set_tool_digital_output(self, pin: int, value: int) -> bool:
        response = self._robot.set_tool_digital_output(pin, value)
        return bool(response["success"])

    def set_payload(self, payload: Kilograms) -> bool:
        response = self._robot.set_payload(payload)
        return bool(response["success"])

    def create_sequence(self) -> RosRobotClient.SequenceBuilder:
        return self._robot.create_sequence()

    def on_system_state_change(self, callback: Callable[[RobotOperationalState, RobotSafetyState], None]) -> int:
        return int(self._robot.on_state_change(callback))

    def movej(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        self._robot.movej(target, velocity, acceleration)

    def movel(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: CartesianPose | None = None,
    ) -> None:
        self._robot.movel(target, velocity, acceleration, reference_frame)

    def movej_async(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
    ) -> None:
        self._robot.movej(target, velocity, acceleration, is_async=True)

    def movel_async(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: CartesianPose | None = None,
    ) -> None:
        self._robot.movel(target, velocity, acceleration, reference_frame, is_async=True)

    def execute_sequence(self, sequence: ISequenceBuilder) -> bool:
        if isinstance(sequence, RosRobotClient.SequenceBuilder):
            return self._robot.execute_sequence(sequence)

        raise TypeError("The sequence must be a SequenceBuilder, not a SequenceBuilderWrapper.")

    def execute_sequence_async(self, sequence: ISequenceBuilder) -> bool:
        if isinstance(sequence, RosRobotClient.SequenceBuilder):
            return self._robot.execute_sequence(sequence, is_async=True)

        raise TypeError("The sequence must be a SequenceBuilder, not a SequenceBuilderWrapper.")

    def wait_for_motion_completion(self, timeout: float | None = None) -> bool:
        return self._robot.wait_for_motion_completion(timeout=timeout)

    def teach_mode(self) -> RosRobotClient._WithTeach:
        return self._robot.teach_mode()

    def reconnect(self, timeout: float | None = 15) -> bool:
        return self._api.reconnect_robot(robot_uuid=self._configuration.uuid, timeout=timeout)
