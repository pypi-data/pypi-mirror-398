from enum import Enum
from typing import Any, TypedDict, Union

from typing_extensions import NotRequired


class Estop(str, Enum):
    UNKNOWN = "Unknown"
    TRIGGERED = "Triggered"
    RELEASED = "Released"


class DetectedNetwork(TypedDict):
    """Dictionary representing the details of detected network"""

    friendlyName: Any
    drivesEnergized: Any
    motorSizes: Any
    driveErrors: Any


class EstopStatus(TypedDict):
    """Dictionary representing the details of estop status"""

    estop: Estop
    areSmartDrivesReady: bool
    detectedNetworks: NotRequired[Union[list[DetectedNetwork], None]]
