# Ignore mypy and pylint all errors
# mypy: ignore-errors
# pylint: disable-all


"""nb
A NOTE ON UNITS:
    All joint angle arguments and return values to methods on class Robot are assumed to be in degrees.
    All cartesian pose arguments and return values are assumed to be of the form
        [x, y, z, rx, ry, rz]
    where:
        x, y, z - millimeters.
        rx, ry, rz - euler XYZ angles in degrees.
    Some unit conversion helpers for unit conversion are provided in the Utils class.
    euler_angle_order:
    Up to 3 characters belonging to the set {‘X’, ‘Y’, ‘Z’} for intrinsic rotations, or {‘x’, ‘y’, ‘z’} for extrinsic rotations. Extrinsic and intrinsic rotations cannot be mixed in one function call.
    default: XYZ
    # a note on "XYZ" vs. "xyz" (intrinsic vs. extrinsic rotations)
    # https://github.com/facebookresearch/pytorch3d/issues/649#issuecomment-916794895
"""

import time
import warnings
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import requests
import roslibpy

from machinelogic.ivention.exception import RobotException
from machinelogic.ivention.igeneric_joint_constraint import IGenericJointConstraint
from machinelogic.ivention.irobot import (
    IRobotAlarm,
    ISequenceBuilder,
    RobotOperationalState,
    RobotSafetyState,
    TeachModeContextManager,
)
from machinelogic.ivention.types.robot_position_data import Timestamp
from machinelogic.ivention.types.robot_types import (
    CartesianPose,
    Degrees,
    DegreesPerSecond,
    DegreesPerSecondSquared,
    DegreesPerSecondSquaredVector,
    DegreesPerSecondVector,
    JointAnglesDegrees,
    Kilograms,
    Millimeters,
    MillimetersPerSecond,
    MillimetersPerSecondSquared,
    ScaleFactor,
)
from machinelogic.machinelogic.robot.robot_utils import AngleUnit, DistanceUnit, Utils
from machinelogic.machinelogic.utils.robot_transforms import (
    transform_position_between_ref_frames,
)

# Default parameters
DOCKER_LAUNCHER_PORT: int = 9090
DOCKER_CONTAINER_PORT: int = 9091
_MAX_BLEND_FRACTION: float = 0.47  # max blend half a move.


# Comes from: https://github.com/VentionCo/vention_ros/blob/develop/VENTION_API.md
class PublicAPI:
    class Service:
        MoveSequence = "vention_robots/move_sequence"
        MoveStop = "vention_robots/move_stop"
        ComputeFK = "vention_robots/compute_fk"
        ComputeIK = "vention_robots/compute_ik"
        SetTCPOffset = "vention_robots/set_tcp_offset"
        GetTCPOffset = "vention_robots/get_tcp_offset"
        SetStartState = "vention_robots/set_start_state"
        GetJointPosition = "vention_robots/get_joint_position"
        GetJointVelocityLimits = "vention_robots/get_joint_velocity_limits"
        GetJointAccelerationLimits = "vention_robots/get_joint_acceleration_limits"
        GetCartesianPosition = "vention_robots/get_cartesian_position"
        GetCartesianVelocityLimit = "vention_robots/get_cartesian_velocity_limit"
        GetCartesianAccelerationLimit = "vention_robots/get_cartesian_acceleration_limit"
        ResetToNormal = "vention_robots/set_robot_operational_state_to_normal"
        ResetToFreedrive = "vention_robots/set_robot_operational_state_to_freedrive"
        GetToolDigitalInput = "vention_robots/get_tool_digital_input"
        SetToolDigitalOutput = "vention_robots/set_tool_digital_output"
        SetPayload = "vention_robots/set_payload"

    class Topic:
        RobotState = "/vention_robots/robot_state"
        RobotAlarm = "/vention_robots/robot_alarm"

    class Type:
        ForwardKinematics = "robot_commands_api/ForwardKinematics"
        InverseKinematics = "robot_commands_api/InverseKinematics"
        GetCartesianLimit = "robot_commands_api/GetCartesianLimit"
        GetCurrentPosJ = "robot_commands_api/GetCurrentPosJ"
        GetCurrentPosX = "robot_commands_api/GetCurrentPosX"
        GetDigitalIO = "robot_commands_api/GetDigitalIO"
        GetJointLimits = "robot_commands_api/GetJointLimits"
        GetTCPOffset = "robot_commands_api/GetTcpOffset"
        MoveControl = "robot_commands_api/MoveControl"
        MoveSequence = "robot_commands_api/MoveSequence"
        ResetRobotState = "robot_commands_api/ResetRobotState"
        SetDigitalIO = "robot_commands_api/SetDigitalIO"
        SetPayload = "robot_commands_api/SetPayload"
        SetTCPOffset = "robot_commands_api/SetTcpOffset"


@dataclass
class RobotAlarm(IRobotAlarm):
    class Level(Enum):
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"

    level: Level
    error_code: int
    description: str

    @staticmethod
    def into(data: Any) -> "RobotAlarm":
        """
        Convert a dictionary into a RobotAlarm object.

        Args:
            data: Dictionary containing the alarm data

        Returns:
            RobotAlarm object
        """
        return RobotAlarm(
            RobotAlarm.Level(data["level"]),
            int(data["error_code"]),
            str(data["description"]),
        )


class RobotModel(Enum):
    """Supported robot models."""

    CRX_10IA = "crx10ia"
    CRX_25IA = "crx25ia"
    M710_IC45M = "m710ic45m"
    M20_ID35 = "m20id35"
    DOOSAN_H2017 = "doosan_h2017"
    UR3_E = "ur3_e"
    UR5_E = "ur5_e"
    UR10_E = "ur10_e"


class ContainerManager:
    # "ContainerManager" - manage and control docker containers
    # via the docker-multi-instance-run-server
    # https://github.com/VentionCo/docker-multi-instance-run-server
    def __init__(self, host="localhost", port=DOCKER_LAUNCHER_PORT):
        self.path = f"http://{host}:{port}"

    def list(self):
        # list processes: docker ps
        lResponse = requests.get(self.path + "/ps")
        return lResponse.json()

    def status(self, container_port: int = DOCKER_CONTAINER_PORT):
        lParams = {"containerPort": container_port}
        lResponse = requests.get(self.path + "/status", params=lParams)
        return lResponse.json()

    def run(
        self,
        robot_model: RobotModel,
        robot_ip: str,
        tool_collision_box_xyz: List[float] = [0.0, 0.0, 0.0],
        tool_collision_box_offset_xyz: List[float] = [0.0, 0.0, 0.0],
        container_port: int = DOCKER_CONTAINER_PORT,
    ):
        lParams = {
            "containerPort": container_port,
            "robotType": robot_model.value,
            "robotIp": robot_ip,
            "toolCollisionBoxXyz": tool_collision_box_xyz,
            "toolCollisionBoxOffsetXyz": tool_collision_box_offset_xyz,
        }
        lResponse = requests.get(self.path + "/run", params=lParams)
        return lResponse.json()

    def _run_doosan(self, robot_ip: str = "192.168.137.100"):
        # run w/ our Doosan configuration.
        return self.run(RobotModel.DOOSAN_H2017, robot_ip=robot_ip)

    def stop(self, container_port: int = DOCKER_CONTAINER_PORT):
        lParams = {
            "containerPort": container_port,
        }
        lResponse = requests.get(self.path + "/stop", params=lParams)
        return lResponse.json()

    def restart(self, container_port: int = DOCKER_CONTAINER_PORT):
        lResponse = requests.post(self.path + f"/restart/{container_port}")
        return lResponse.json()

    def is_running(self, container_port: int = DOCKER_CONTAINER_PORT):
        lStatus = self.status(container_port)
        if not lStatus["success"]:
            return False
        return lStatus["state"]["Status"] == "running"


class _MoveType(Enum):
    J = 1  # movej
    L = 2  # movel


class _PositionType(Enum):
    Joint = 1  # [j1, j2, j3, j4, j5, j6] (rad)
    Cartesian = 2  # [x, y, z, rx, ry, rz, rw] (meters, quaternions)


class _MoveReference(Enum):
    World = "world"
    # LINK = "tcp_link"


def _get_moveit_move_message(
    move_type: _MoveType,
    pos_type: _PositionType,
    pos_data: List[float],
    ref: _MoveReference,
    vel_scale: ScaleFactor,
    acc_scale: ScaleFactor,
    time: float,
    radius: Millimeters,
) -> Dict:
    pos_msg = {"type": pos_type.value, "data": pos_data, "ref": ref.value}
    return {
        "type": move_type.value,
        "pos": pos_msg,
        "vel_scale": vel_scale,
        "acc_scale": acc_scale,
        "time": time,
        "radius": radius,
    }


def _get_movej_message(
    joint_angles: JointAnglesDegrees,
    velocity_scale: ScaleFactor,
    acceleration_scale: ScaleFactor,
    time: float = 0.0,
    blend_radius_mm: Millimeters = 0.0,
) -> Dict:
    joint_angles_rad = Utils.to_radians(joint_angles)
    blend_radius_m = Utils.to_meters([blend_radius_mm], from_units=DistanceUnit.Millimeters)[0]

    return _get_moveit_move_message(
        _MoveType.J,
        _PositionType.Joint,
        joint_angles_rad,
        _MoveReference.World,
        velocity_scale,
        acceleration_scale,
        time,
        blend_radius_m,
    )


def _get_movel_message(
    cartesian_pose: CartesianPose,
    velocity_scale: ScaleFactor,
    acceleration_scale: ScaleFactor,
    time: float = 0.0,
    blend_radius_mm: Millimeters = 0.0,
) -> Dict:
    cartesian_pose_quaternions_rad = _to_moveit_cartesian_pose(cartesian_pose)
    blend_radius_m = Utils.to_meters([blend_radius_mm], from_units=DistanceUnit.Millimeters)[0]
    return _get_moveit_move_message(
        _MoveType.L,
        _PositionType.Cartesian,
        cartesian_pose_quaternions_rad,
        _MoveReference.World,
        velocity_scale,
        acceleration_scale,
        time,
        blend_radius_m,
    )


class Listener:
    def __init__(self):
        self.handlers = {}
        self.id = 0

    def register(self, pHandler: Callable) -> int:
        lIndex = self.id
        self.handlers[lIndex] = pHandler
        self.id += 1
        return lIndex

    def remove(self, pIndex) -> None:
        if pIndex in self.handlers:
            del self.handlers[pIndex]

    def handle(self, *args, **kwargs):
        for lHandlerIndex in self.handlers:
            self.handlers[lHandlerIndex](*args, **kwargs)


def _to_moveit_cartesian_pose(
    position_and_euler_angles: CartesianPose,
) -> List[float]:
    # prepare position for sending to moveit (millis, euler_XYZ_degree) -> (meters, quaternions_rad)
    position_meters = Utils.to_meters(position_and_euler_angles[:3], from_units=DistanceUnit.Millimeters)
    quaternions_rad = Utils.to_quaternions(position_and_euler_angles[3:])

    return position_meters + quaternions_rad


def _from_moveit_cartesian_pose(
    position_from_moveit: List[float],
) -> CartesianPose:
    # [x, y, z] (Meters) + [x, y, z, w] (quaternions, radians)
    # return as [x, y, z] (Millimeters) + [Z, Y, Z] (euler)
    position = Utils.to_millimeters(position_from_moveit[0:3])
    euler_angles = Utils.to_degrees(Utils.to_euler_angles(position_from_moveit[3:], order="XYZ", angle_units=AngleUnit.Radians))
    return position + euler_angles


def _to_moveit_joint_constraints(
    incoming_joint_constraints: List[IGenericJointConstraint],
) -> List[Dict]:
    # prepare joint constraints for sending to moveit (index-base-1, deg) -> (index-base-0, rad).
    joint_constraints = []
    for joint_constraint in incoming_joint_constraints:
        joint_index_base_0 = joint_constraint.joint_index - 1
        joint_constraints.append(
            {
                "joint_index": joint_index_base_0,
                "position": Utils.to_radians([joint_constraint.position])[0],
                "tolerance_above": Utils.to_radians([joint_constraint.tolerance_above])[0],
                "tolerance_below": Utils.to_radians([joint_constraint.tolerance_below])[0],
                "weight": joint_constraint.weighting_factor,
            }
        )
    return joint_constraints


class _Move:
    # internal representation of a generic move.
    def __init__(
        self,
        move_type: _MoveType,
        target: Union[CartesianPose, JointAnglesDegrees],
        velocity: Union[DegreesPerSecond, MillimetersPerSecond],
        acceleration: Union[DegreesPerSecondSquared, MillimetersPerSecondSquared],
        blend_radius: Millimeters,
    ):
        self.move_type = move_type
        self.target = target
        self.velocity = velocity
        self.acceleration = acceleration
        self.blend_radius = blend_radius

    def message(
        self,
        angular_velocity_limit: DegreesPerSecond,
        angular_acceleration_limit: DegreesPerSecondSquared,
        cartesian_velocity_limit: MillimetersPerSecond,
        cartesian_acceleration_limit: MillimetersPerSecondSquared,
        blend_radius: Millimeters,
    ) -> Dict:
        # return MoveIt formatted message.
        if _MoveType.J == self.move_type:
            velocity_scale = Utils.angular_velocity_to_scale_factor(self.velocity, angular_velocity_limit)
            acceleration_scale = Utils.angular_acceleration_to_scale_factor(self.acceleration, angular_acceleration_limit)
            return _get_movej_message(
                self.target,
                velocity_scale,
                acceleration_scale,
                blend_radius_mm=blend_radius,
            )
        if _MoveType.L == self.move_type:
            velocity_scale = Utils.cartesian_velocity_to_scale_factor(cast(MillimetersPerSecond, self.velocity), cartesian_velocity_limit)
            acceleration_scale = Utils.angular_acceleration_to_scale_factor(
                cast(MillimetersPerSecondSquared, self.acceleration),
                cartesian_acceleration_limit,
            )
            return _get_movel_message(
                self.target,
                velocity_scale,
                acceleration_scale,
                blend_radius_mm=blend_radius,
            )
        raise Exception(f"Invalid move_type: {self.move_type}")


class RosRobotClient:
    OperationalState = RobotOperationalState
    SafetyState = RobotSafetyState

    class SequenceBuilder(ISequenceBuilder):
        """A builder for a sequence of moves."""

        def __init__(self, robot: Union["RosRobotClient", None] = None):
            self.robot = robot
            self.sequence: List[_Move] = []
            self.is_async_at_execute: bool = False

        def append_movej(
            self,
            target: JointAnglesDegrees,
            velocity: DegreesPerSecond = 10.0,
            acceleration: DegreesPerSecondSquared = 10.0,
            blend_radius: Millimeters = 0.0,
        ) -> "RosRobotClient.SequenceBuilder":
            """
            Append a movej to the sequence.

            Args:
                target (JointAnglesDegrees): The target joint angles, in degrees.
                velocity (DegreesPerSecond): The velocity of the move, in degrees per second. Defaults to 10.0.
                acceleration (DegreesPerSecondSquared): The acceleration of the move, in degrees per second squared. Defaults to 10.0.
                blend_radius (Millimeters): The blend radius of the move, in millimeters. Defaults to 0.0.

            Returns:
                SequenceBuilder: The builder.
            """
            self.sequence.append(
                _Move(
                    _MoveType.J,
                    target,
                    velocity,
                    acceleration,
                    blend_radius,
                )
            )
            return self

        def append_movel(
            self,
            target: CartesianPose,
            velocity: MillimetersPerSecond = 100.0,
            acceleration: MillimetersPerSecondSquared = 100.0,
            blend_radius: Millimeters = 0.0,
            reference_frame: Union[CartesianPose, None] = None,
        ) -> "RosRobotClient.SequenceBuilder":
            """
            Append a movel to the sequence.

            Args:
                target (CartesianPose): The target pose.
                velocity (MillimetersPerSecond): The velocity of the move, in millimeters per second. Defaults to 100.0.
                acceleration (MillimetersPerSecondSquared): The acceleration of the move, in millimeters per second squared. Defaults to 100.0.
                blend_radius (Millimeters): The blend radius of the move, in millimeters. Defaults to 0.0.
                reference_frame (CartesianPose): The reference frame for the target pose. Defaults to None.

            Returns:
                SequenceBuilder: The builder.
            """
            if reference_frame is None:
                reference_frame = [0.0] * 6
            target_wrt_ref = transform_position_between_ref_frames(target, from_reference_frame=reference_frame)
            self.sequence.append(
                _Move(
                    _MoveType.L,
                    target_wrt_ref,
                    velocity,
                    acceleration,
                    blend_radius,
                )
            )
            return self

        def __enter__(self) -> "RosRobotClient.SequenceBuilder":
            return self

        def __exit__(
            self,
            exc_type: Any,
            exc_value: Any,
            traceback: Any,
        ) -> Any:
            if self.robot is not None:
                self.robot.execute_sequence(self, is_async=self.is_async_at_execute)
            # clean up is_async_at_execute flag.
            self.is_async_at_execute = False

    class _WithTeach(TeachModeContextManager):
        def __init__(self, robot: "RosRobotClient"):
            self.robot = robot
            self.robot.start_teach_mode()

        def __enter__(self):
            pass

        def __exit__(
            self,
            exc_type: Any,
            exc_value: Any,
            traceback: Any,
        ) -> Any:
            self.robot.reset()
            return True

    def __init__(
        self,
        model: RobotModel = RobotModel.DOOSAN_H2017,
        pendant_ip: str = "192.168.137.52",
        robot_controller_ip: str = "192.168.137.100",
        port: int = DOCKER_CONTAINER_PORT,
        on_state_change: Union[None, Callable[[RobotOperationalState, RobotSafetyState], None]] = None,
        on_log_alarm: Union[None, Callable[[RobotAlarm], None]] = None,
        skip_container_management: bool = False,
    ):
        self._skip_container_management = skip_container_management
        self._pendant_ip = pendant_ip
        self._robot_controller_ip = robot_controller_ip
        self._port = port

        # Move sequence.
        self.move_in_progress = False
        self.async_move_error: Union[None, str] = None

        self.container_mananger = ContainerManager(host=pendant_ip)
        if not skip_container_management:
            if not self.container_mananger.is_running():
                # start container with desired parameters.
                self.container_mananger.run(model, robot_controller_ip, container_port=port)

        # topic listeners.
        self.state_listener = Listener()
        self.state_listener.register(lambda x: self._handle_state(x))
        self.log_listener = Listener()
        self._default_log_handler = self.log_listener.register(
            (lambda data: warnings.warn("unhandled log alarm:\n" + str(data))) if on_log_alarm is None else on_log_alarm
        )
        if on_state_change is not None:
            self.on_state_change(on_state_change)

        self._init_ros_client()
        return

    def _init_ros_client(self):
        self.robot_state = RobotOperationalState.OFFLINE
        self.safety_state = RobotSafetyState.UNKNOWN
        self.client = roslibpy.Ros(host=self._pendant_ip, port=self._port)
        self.client.run(timeout=30)
        # get topic listeners.
        state_topic_listener = self._get_topic_listener(PublicAPI.Topic.RobotState)
        log_topic_listener = self._get_topic_listener(PublicAPI.Topic.RobotAlarm)

        # register callbacks
        log_topic_listener.subscribe(lambda data: self.log_listener.handle(RobotAlarm.into(data)))
        state_topic_listener.subscribe(lambda data: self.state_listener.handle(data))

        # cache speed limits for move calculations.
        self._joint_velocity_limit = self.get_joint_velocity_limit()
        self._joint_acceleration_limit = self.get_joint_acceleration_limit()
        self._cartesian_velocity_limit = self.get_cartesian_velocity_limit()
        self._cartesian_acceleration_limit = self.get_cartesian_acceleration_limit()

    # todo: rename to user friendly: "restart_connection"
    # todo: test (container restart might take a while).
    def restart_container(self):
        if self._skip_container_management:
            warnings.warn("skip_container_management = True, skipping attempt to restart container.")
            return
        self.container_mananger.restart(container_port=self._port)
        self._init_ros_client()
        return

    def _handle_state(self, pMessage):
        self.robot_state = RobotOperationalState(pMessage["operational_state"])
        self.safety_state = RobotSafetyState(pMessage["safety_state"])

    # ROS utilities.
    def _get_topics(self):
        return self.client.get_topics()

    def _get_services(self):
        return self.client.get_services()

    def _get_service_type(self, pService) -> str:
        return self.client.get_service_type(pService)

    def _get_topic_type(self, pTopic) -> str:
        return self.client.get_topic_type(pTopic)

    def _call_service(
        self,
        service_name: str,
        service_type: str,
        request: Any = roslibpy.ServiceRequest(),
        timeout: Optional[Union[int, float]] = 30,  # seconds.
    ) -> Any:
        service = roslibpy.Service(self.client, service_name, service_type)
        return service.call(request, timeout=timeout)

    def _call_service_async(
        self,
        service_name: str,
        service_type: str,
        async_callback: Callable[[Any, Any], None],  # callback: fn (result, error) -> None
        request: Any = roslibpy.ServiceRequest(),
    ) -> Any:
        service = roslibpy.Service(self.client, service_name, service_type)
        return service.call(
            request,
            (lambda result: async_callback(result, None)),
            (lambda error: async_callback(None, error)),
        )

    def _get_topic_listener(self, pTopic: str):
        lType = self._get_topic_type(pTopic)
        lListener = roslibpy.Topic(self.client, pTopic, lType)
        # call roslibpy.subscribe(callback)
        return lListener

    # public:

    # set log alarm listener callback
    def on_log_alarm(self, callback: Callable[[RobotAlarm], None]) -> int:
        handler_id = self.log_listener.register(callback)
        if self._default_log_handler is not None:
            # clear out "UNHANDLED LOG ALARM"
            self.log_listener.remove(self._default_log_handler)
            self._default_log_handler = None
        return handler_id

    # set robot state change callback
    def on_state_change(self, callback: Callable[[RobotOperationalState, RobotSafetyState], None]) -> int:
        def _handler(data: Dict):
            callback(
                RobotOperationalState(data["operational_state"]),
                RobotSafetyState(data["safety_state"]),
            )

        return self.state_listener.register(_handler)

    # jog <joint_angle> degrees on joint <joint_index>.
    def jog(
        self,
        joint_index: int,
        jog_angle: Degrees,
        velocity: DegreesPerSecond = 10.0,
    ):
        target_position, _ = self.get_joint_positions()
        target_position[joint_index] = jog_angle
        return self.movej(target_position, velocity=velocity)

    # jog <jog_unit> millimeters/degrees from current position in coordinate_index (0-x, 1-y, 2-z, 3-euler_z1, 4-euler_y, 5-euler_z2)
    def linear_jog(
        self,
        coordinate_index: int,
        jog_unit: Millimeters,
        velocity: MillimetersPerSecond = 50.0,
    ):
        jog_target, _ = self.get_cartesian_position()
        jog_target[coordinate_index] += jog_unit
        return self.movel(jog_target, velocity=velocity)

    # reset the robot state.
    def reset(self) -> Dict:
        # >>> r.reset()
        # {'response': 'NONE', 'success': True}
        return self._call_service(
            PublicAPI.Service.ResetToNormal,
            PublicAPI.Type.ResetRobotState,
            dict(),
            timeout=15,
        )

    def set_tcp_offset(self, tcp_offset, order="XYZ") -> Any:
        tcp_offset[:3] = [x / DistanceUnit.Meters.value for x in tcp_offset[:3]]
        quaternion = Utils.to_quaternions(tcp_offset[3:], euler_angle_order=order)
        # append quaternion list to te end of tcp_offset list
        tcp_offset_quaternion = [0.0] * 7
        tcp_offset_quaternion[:3] = tcp_offset[:3]
        tcp_offset_quaternion[3:] = quaternion
        return self._call_service(
            PublicAPI.Service.SetTCPOffset,
            PublicAPI.Type.SetTCPOffset,
            dict(tcp_offset=tcp_offset_quaternion),
        )

    def get_tcp_offset(self) -> CartesianPose:
        pose = self._call_service(
            PublicAPI.Service.GetTCPOffset,
            PublicAPI.Type.GetTCPOffset,
        )["tcp_offset"]

        # Convert to mm and deg
        return _from_moveit_cartesian_pose(pose)

    # get the current joint position.
    def get_joint_positions(self) -> Tuple[JointAnglesDegrees, Timestamp]:
        resp = self._call_service(
            PublicAPI.Service.GetJointPosition,
            PublicAPI.Type.GetCurrentPosJ,
        )
        lRadPosition: List[float] = resp["position"]
        stamp = resp["stamp"]
        return (Utils.to_degrees(lRadPosition), Timestamp.into(stamp))

    # get the current robot state.
    def get_robot_state(self) -> RobotOperationalState:
        return self.robot_state

    def get_safety_state(self) -> RobotSafetyState:
        return self.safety_state

    def get_move_in_progress(self) -> bool:
        return self.move_in_progress

    # get the current cartesian position.
    def get_cartesian_position(self) -> Tuple[CartesianPose, Timestamp]:
        resp = self._call_service(
            PublicAPI.Service.GetCartesianPosition,
            PublicAPI.Type.GetCurrentPosX,
        )
        lPosition = resp["position"]
        stamp = resp["stamp"]
        return (_from_moveit_cartesian_pose(lPosition), Timestamp.into(stamp))

    def teach_mode(self) -> _WithTeach:
        # usage:
        # with robot.teach_mode():
        #   ... do things in teach mode ...
        # # automatically exists teach mode.
        return RosRobotClient._WithTeach(self)

    # enter teach mode on the robot for guided jogging.
    def start_teach_mode(self):
        return self._call_service(
            PublicAPI.Service.ResetToFreedrive,
            PublicAPI.Type.ResetRobotState,
        )

    # exit teach mode on the robot to finish guided jogging.
    def exit_teach_mode(self):
        return self.reset()

    def _move_sequence(
        self,
        move_messages: List[Dict],
        is_async: bool = False,
    ):
        if self.move_in_progress:
            self.move_stop()
            raise Exception("Cannot perform new move sequence while async move sequence is in progress")

        self.move_in_progress = True
        if is_async:
            return self._call_service_async(
                service_name=PublicAPI.Service.MoveSequence,
                service_type=PublicAPI.Type.MoveSequence,
                async_callback=self._handle_move_sequence_result,
                request=dict(moves=move_messages),
            )
        else:
            return self._call_service(
                PublicAPI.Service.MoveSequence,
                PublicAPI.Type.MoveSequence,
                dict(moves=move_messages),
                timeout=None,
            )

    def _handle_move_sequence_result(self, result: Optional[Any], error: Optional[Any]):
        self.move_in_progress = False
        if result is not None:
            return
        elif error is not None:
            self.async_move_error = f"Async robot move sequence failed: {error}"
        else:
            self.async_move_error = "Async move sequence failed with no result or error"

    # forward kinematics (joint position to cartesian position).
    def forward_kinematics(
        self,
        joint_position: JointAnglesDegrees,
    ) -> CartesianPose:
        ref: int = 0
        joint_position_rad = Utils.to_radians(joint_position)
        fk_result = self._call_service(
            PublicAPI.Service.ComputeFK,
            PublicAPI.Type.ForwardKinematics,
            dict(pos=joint_position_rad, ref=ref),
            timeout=180,
        )["conv_posx"]
        return _from_moveit_cartesian_pose(fk_result)

    # inverse kinematics (cartesian position to joint position).
    def inverse_kinematics(
        self,
        cartesian_position: CartesianPose,
        joint_constraints: Union[None, List[IGenericJointConstraint]] = None,
        seed_position: Union[JointAnglesDegrees, None] = None,
    ) -> JointAnglesDegrees:
        ref: int = 0
        solution_space: int = 0
        quat_position = _to_moveit_cartesian_pose(cartesian_position)
        move_it_joint_constraints = _to_moveit_joint_constraints(joint_constraints) if joint_constraints else []
        seed_position_rad = Utils.to_radians(seed_position) if seed_position else []
        ik_result = self._call_service(
            PublicAPI.Service.ComputeIK,
            PublicAPI.Type.InverseKinematics,
            dict(
                pos=quat_position,
                joint_constraints=move_it_joint_constraints,
                joint_seed_position=seed_position_rad,
                sol_space=solution_space,
                ref=ref,
            ),
            timeout=180,
        )["conv_posj"]
        return Utils.to_degrees(ik_result)

    # get maximum cartesian velocity (mm/s).
    def get_cartesian_velocity_limit(self) -> MillimetersPerSecond:
        """
        :return: cartesian translational velocity limit (m/s) if successful, None otherwise
        """
        return (
            self._call_service(
                PublicAPI.Service.GetCartesianVelocityLimit,
                PublicAPI.Type.GetCartesianLimit,
            )["cartesian_limit"]
            * 1000.0
        )

    # get maximum cartesian acceleration (mm/s^2).
    def get_cartesian_acceleration_limit(self) -> MillimetersPerSecondSquared:
        """
        :return: cartesian translational acceleration limit (m/s^2) if successful, None otherwise
        """
        return (
            self._call_service(
                PublicAPI.Service.GetCartesianAccelerationLimit,
                PublicAPI.Type.GetCartesianLimit,
            )["cartesian_limit"]
            * 1000.0
        )

    # get maximum joint velocity (List[deg/s]).
    def get_joint_velocity_limit(self) -> DegreesPerSecondVector:
        """
        :return: [v1, v2, v3, v4, v5, v6] (rad/s) if successful, None otherwise
        """
        return Utils.to_degrees(
            self._call_service(
                PublicAPI.Service.GetJointVelocityLimits,
                PublicAPI.Type.GetJointLimits,
            )["joint_limits"]
        )

    # get maximum joint acceleration (List[deg/s^2]).
    def get_joint_acceleration_limit(self) -> DegreesPerSecondSquaredVector:
        """
        :return: [a1, a2, a3, a4, a5, a6] (rad/s^2) if successful, None otherwise
        """
        return Utils.to_degrees(
            self._call_service(
                PublicAPI.Service.GetJointAccelerationLimits,
                PublicAPI.Type.GetJointLimits,
            )["joint_limits"]
        )

    def set_tool_digital_output(self, pin: int, value: int):
        return self._call_service(
            PublicAPI.Service.SetToolDigitalOutput,
            PublicAPI.Type.SetDigitalIO,
            dict(index=pin, value=value),
        )

    def get_tool_digital_input(self, pin: int) -> bool:
        return (
            self._call_service(
                PublicAPI.Service.GetToolDigitalInput,
                PublicAPI.Type.GetDigitalIO,
                dict(index=pin),
            )["value"]
            == 1
        )

    def set_payload(
        self,
        payload: Kilograms,
    ):
        return self._call_service(
            PublicAPI.Service.SetPayload,
            PublicAPI.Type.SetPayload,
            dict(payload=payload),
        )

    def create_sequence(self) -> "RosRobotClient.SequenceBuilder":
        return RosRobotClient.SequenceBuilder(robot=self)

    def execute_sequence(self, sequence: "RosRobotClient.SequenceBuilder", is_async: bool = False) -> bool:
        moves = sequence.sequence
        if len(moves) == 0:
            raise Exception("no moves in sequence")
        limits = (
            self._joint_velocity_limit,
            self._joint_acceleration_limit,
            self._cartesian_velocity_limit,
            self._cartesian_acceleration_limit,
        )
        blend_radii = self._calculate_blend_radii(moves)
        move_messages = [move.message(*limits, blend_radii[index]) for index, move in enumerate(moves)]
        response = self._move_sequence(move_messages=move_messages, is_async=is_async)
        # if executing an async move, the response will be None
        if is_async and response is None:
            return True
        self.move_in_progress = False
        result = response["result"]
        status_code, description = result["status_code"], result["description"]
        if status_code != 1:
            raise RobotException(f"execute_sequence failed (code: {status_code}): {description}")
        return True

    def movej(
        self,
        target: JointAnglesDegrees,
        velocity: DegreesPerSecond = 10.0,
        acceleration: DegreesPerSecondSquared = 10.0,
        is_async: bool = False,
    ):
        with self.create_sequence() as seq:
            seq.is_async_at_execute = is_async
            seq.append_movej(target, velocity=velocity, acceleration=acceleration)

    def movel(
        self,
        target: CartesianPose,
        velocity: MillimetersPerSecond = 100.0,
        acceleration: MillimetersPerSecondSquared = 100.0,
        reference_frame: Union[CartesianPose, None] = None,
        is_async: bool = False,
    ):
        with self.create_sequence() as seq:
            seq.is_async_at_execute = is_async
            seq.append_movel(
                target,
                velocity=velocity,
                acceleration=acceleration,
                reference_frame=reference_frame,
            )

    def wait_for_motion_completion(self, timeout: Union[float, None] = None) -> bool:
        start_time = time.time()

        while self.get_move_in_progress():
            time.sleep(0.05)
            elapsed_time = time.time() - start_time
            if timeout is not None and elapsed_time >= timeout:
                return False

        if self.async_move_error is not None:
            error_to_raise = self.async_move_error
            self.async_move_error = None
            raise RobotException(error_to_raise)

        return True

    def move_stop(self) -> bool:
        response = self._call_service(
            PublicAPI.Service.MoveStop,
            PublicAPI.Type.MoveControl,
        )
        self.move_in_progress = False
        return bool(response["success"])

    def _pose_for_move(self, move: _Move) -> CartesianPose:
        if _MoveType.J == move.move_type:
            return self.forward_kinematics(move.target)
        return move.target

    def _calculate_blend_radii(self, move_sequence: List[_Move]) -> List[Millimeters]:
        current_position, _ = self.get_cartesian_position()
        move_poses: List[CartesianPose] = [self._pose_for_move(move) for move in move_sequence]
        blend_radii: List[Millimeters] = [0.0] * len(move_sequence)

        for index, move in enumerate(move_sequence):
            if index == len(move_sequence) - 1:
                # last radius is, necessarily, zero.
                blend_radii[index] = 0.0
                break
            target_pose = move_poses[index]
            distance_to_prev_point = Utils.get_distance(target_pose, current_position if index == 0 else move_poses[index - 1])
            distance_to_next_point = Utils.get_distance(target_pose, move_poses[index + 1])
            minimum_blend_distance = min(distance_to_prev_point, distance_to_next_point)
            blend_radii[index] = min(minimum_blend_distance * _MAX_BLEND_FRACTION, move.blend_radius)
        return blend_radii
