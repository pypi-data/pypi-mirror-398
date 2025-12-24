# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
from enum import Enum
from typing import TypedDict


class UnitOfDistance(str, Enum):
    METERS = "Meters"
    MILLIMETERS = "Millimeters"


DISTANCE_PER_METER: dict[UnitOfDistance, float] = {
    UnitOfDistance.METERS: 1,
    UnitOfDistance.MILLIMETERS: 1000,
}


class Distance(TypedDict):
    value: float
    unit: UnitOfDistance


def convert_distance(value: float, old_unit: UnitOfDistance, new_unit: UnitOfDistance) -> "Distance":
    new_value = value * DISTANCE_PER_METER[new_unit] / DISTANCE_PER_METER[old_unit]
    return Distance(value=new_value, unit=new_unit)
