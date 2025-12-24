from typing import TypedDict

from ...measurements.angle import Angle
from ...measurements.distance import Distance


class Rotation(TypedDict):
    i: Angle
    j: Angle
    k: Angle


class Position(TypedDict):
    x: Distance
    y: Distance
    z: Distance


class Pose(TypedDict):
    position: Position
    rotation: Rotation
