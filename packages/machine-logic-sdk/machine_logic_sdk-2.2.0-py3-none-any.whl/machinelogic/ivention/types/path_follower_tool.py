from typing import TypedDict, Union

from typing_extensions import NotRequired


class ToolOutputInfo(TypedDict):
    uuid: str
    value: int


class PathFollowerTool(TypedDict):
    """Dictionary representing a path following tool"""

    cw: ToolOutputInfo
    ccw: NotRequired[Union[ToolOutputInfo, None]]
