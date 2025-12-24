import math
from enum import Enum
from typing import List

import numpy as np
from scipy.spatial.transform import Rotation as scipy_rotation

from machinelogic.ivention.types.robot_types import (
    CartesianPose,
    DegreesPerSecond,
    DegreesPerSecondSquared,
    MillimetersPerSecond,
    MillimetersPerSecondSquared,
    ScaleFactor,
)


class RotationType(Enum):
    Euler = 0
    Quaternions = 1


class AngleUnit(Enum):
    Degrees = 0
    Radians = 1


class DistanceUnit(Enum):
    Millimeters = 1.0
    Meters = 1000.0
    Inches = 25.4
    Feet = 304.8
    AstronomicalUnits = 1.496e14


class Utils:
    @staticmethod
    def threshold(value: float, minimum: float, maximum: float) -> float:
        # return a value such that minimum <= value <= maximum
        return max(minimum, min(maximum, value))

    @staticmethod
    def to_radians(degrees: List[float]) -> List[float]:
        return [math.radians(angle) for angle in degrees]

    @staticmethod
    def to_degrees(radians: List[float]) -> List[float]:
        return [math.degrees(angle) for angle in radians]

    @staticmethod
    def to_millimeters(distances: List[float], from_units: DistanceUnit = DistanceUnit.Meters) -> List[float]:
        ratio = from_units.value / DistanceUnit.Millimeters.value
        return [ratio * distance for distance in distances]

    @staticmethod
    def to_meters(
        distances: List[float],
        from_units: DistanceUnit = DistanceUnit.Millimeters,
    ) -> List[float]:
        if from_units is None:
            from_units = DistanceUnit.Millimeters
        ratio = from_units.value / DistanceUnit.Meters.value
        return [ratio * distance for distance in distances]

    @staticmethod
    def to_quaternions(
        euler_angles: List[float],
        euler_angle_order: str = "XYZ",
        angle_units: AngleUnit = AngleUnit.Degrees,
    ) -> List[float]:
        is_degrees = AngleUnit.Degrees == angle_units
        quaternions = list(scipy_rotation.from_euler(euler_angle_order, euler_angles, degrees=is_degrees).as_quat())

        return quaternions

    @staticmethod
    def to_euler_angles(
        quaternions: List[float],
        order: str = "XYZ",
        angle_units: AngleUnit = AngleUnit.Degrees,
    ) -> List[float]:
        is_degrees = AngleUnit.Degrees == angle_units
        euler_angles = scipy_rotation.from_quat(quaternions).as_euler(order, degrees=is_degrees)
        return list(euler_angles)

    @staticmethod
    def get_distance(
        cartesian_pose_a: CartesianPose,
        cartesian_pose_b: CartesianPose,
    ) -> float:
        p1, p2 = np.array(cartesian_pose_a[:3]), np.array(cartesian_pose_b[:3])
        return float(np.linalg.norm(p1 - p2))

    @staticmethod
    def angular_velocity_to_scale_factor(velocity: DegreesPerSecond, limits: DegreesPerSecond) -> ScaleFactor:
        if not isinstance(velocity, list):
            velocity = [velocity] * 6
        if not isinstance(limits, list):
            limits = [limits] * 6
        min_scale = float("inf")
        for i, limit_i in enumerate(limits):
            scale = abs(velocity[i] / limit_i)
            if scale < min_scale:
                min_scale = scale
        return Utils.threshold(min_scale, 0.01, 1.0)

    @staticmethod
    def angular_acceleration_to_scale_factor(
        acceleration: DegreesPerSecondSquared,
        limits: DegreesPerSecondSquared,
    ) -> ScaleFactor:
        return Utils.angular_velocity_to_scale_factor(acceleration, limits)

    @staticmethod
    def cartesian_velocity_to_scale_factor(velocity: MillimetersPerSecond, limit: MillimetersPerSecond) -> ScaleFactor:
        return Utils.threshold(abs(velocity / limit), 0.01, 1.0)

    @staticmethod
    def cartesian_acceleration_to_scale_factor(
        acceleration: MillimetersPerSecondSquared, limit: MillimetersPerSecondSquared
    ) -> ScaleFactor:
        return Utils.cartesian_velocity_to_scale_factor(acceleration, limit)
