# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import math
from enum import Enum
from typing import TypedDict


class UnitOfAngle(str, Enum):
    DEGREE = "Degrees"
    RADIANS = "Radians"


ANGLE_PER_RADIANS: dict[UnitOfAngle, float] = {
    UnitOfAngle.RADIANS: 1,
    UnitOfAngle.DEGREE: 180 / math.pi,
}


class Angle(TypedDict):
    value: float
    unit: UnitOfAngle


def convert_angle(value: float, old_unit: UnitOfAngle, new_unit: UnitOfAngle) -> "Angle":
    new_value = value * ANGLE_PER_RADIANS[new_unit] / ANGLE_PER_RADIANS[old_unit]
    return Angle(value=new_value, unit=new_unit)
