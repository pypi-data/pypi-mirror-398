from typing import Literal, TypedDict

ActuatorType = Literal[
    "belt",
    "rack_and_pinion",
    "rack_and_pinion_v2",
    "ball_screw",
    "enclosed_ball_screw",
    "enclosed_lead_screw",
    "indexer",
    "indexer_v2",
    "electric_cylinder",
    "belt_conveyor",
    "roller_conveyor",
    "pneumatic",
    "ac_motor_with_vfd",
    "enclosed_timing_belt",
    "belt_rack",
    "heavy_duty_roller_conveyor",
    "timing_belt_conveyor",
    "telescopic_column",
    "custom",
]


class ActuatorDetails(TypedDict):
    """Dictionary representing the details of an axis

    Args:
        TypedDict (TypedDict): _description_
    """

    name: str
    uuid: str
    controllerId: str
    ip: str
    parentDrive: int
    childDrives: list[int]
    mmPerRotation: float
    axisType: ActuatorType
    multiplier: float
    tuningProfile: Literal["default", "conveyor_turntable", "custom"]
    motorSize: Literal["Nema 17 Stepper", "Small Servo", "Medium Servo", "Large Servo"]
    controlLoop: str
    motorCurrent: float
    brake: bool
    rotation: Literal[-1, 1]
