from typing import TypedDict, Union


class PathFollowerStatus(TypedDict):
    """Dictionary representing the status of a path follower instance"""

    running: bool
    line: float
    command: str
    speed: float
    acceleration: float
    tool: object
    error: Union[str, None]
