# pylint: disable=duplicate-code
from typing import TypedDict


class PneumaticDetails(TypedDict):
    """
    Dictionary representing the details of a pneumatic
    class PneumaticDetails

    Args:
    TypedDict (TypedDict): _description_
    """

    name: str
    uuid: str
    controllerId: str
    ip: str
    device: int
    pushInPin: int
    pullInPin: int
    pushOutPin: int
    pullOutPin: int
