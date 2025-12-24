# pylint: disable=duplicate-code
from typing import Literal, TypedDict


class DigitalInputDetails(TypedDict):
    """Dictionary representing the details of an input

    Args:
        TypedDict (TypedDict): _description_
    """

    name: str
    uuid: str
    controllerId: str
    ip: str
    device: int
    pin: int
    deviceType: Literal["pushButtonModule", "powerSwitchModule", "digitalIOModule"]
    activeHigh: bool
