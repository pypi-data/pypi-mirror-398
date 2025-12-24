from dataclasses import dataclass
from enum import Enum
from typing import List, Union


class MoveType(str, Enum):
    TRAPEZOIDAL_MOVE = "TrapezoidalMove"
    CONTINUOUS_MOVE = "ContinuousMove"
    TORQUE_MOVE = "TorqueMove"


@dataclass
class TorqueMotionProfile:
    torque_percentage: int


@dataclass
class TrapezoidalMotion:
    motor_address: str
    position_target: float


@dataclass
class TrapezoidalMove:
    motions: List[TrapezoidalMotion]
    use_relative_reference: bool
    motion_profile: dict[str, float]
    ignore_synchronization: bool
    move_type: str = MoveType.TRAPEZOIDAL_MOVE.value


@dataclass
class ContinuousMove:
    motor_address: str
    motion_profile: dict[str, float]
    move_type: str = MoveType.CONTINUOUS_MOVE.value


@dataclass
class TorqueMove:
    motor_address: str
    motion_profile: TorqueMotionProfile
    move_type: str = MoveType.TORQUE_MOVE.value


@dataclass
class BatchMove:
    moves: List[Union[TrapezoidalMove, ContinuousMove, TorqueMove]]
