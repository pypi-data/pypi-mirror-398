from typing import TypedDict


class ACMotorDetails(TypedDict):
    """
    A dictionary representing the details of an AC motor with VFD.

    Args:
        TypedDict (TypedDict): _description_
    """

    name: str
    uuid: str
    ip: str
    controllerId: str
    device: int
    directionOutPin: int
    moveOutPin: int
