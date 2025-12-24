from dataclasses import dataclass
from typing import TypedDict

from machinelogic.ivention.types.robot_types import CartesianPose


class CartesianPoseTypedDict(TypedDict):
    x: float
    y: float
    z: float
    i: float
    j: float
    k: float


class IncomingRobotTCP(TypedDict):
    name: str
    uuid: str
    tcp_offset: CartesianPoseTypedDict


class IncomingActiveTCP(TypedDict):
    tcpUuid: str
    offset: CartesianPoseTypedDict


@dataclass
class CartesianPoseObject:
    x: float
    y: float
    z: float
    i: float
    j: float
    k: float


@dataclass
class RobotTCP:
    name: str
    uuid: str
    tcp_offset: CartesianPose
