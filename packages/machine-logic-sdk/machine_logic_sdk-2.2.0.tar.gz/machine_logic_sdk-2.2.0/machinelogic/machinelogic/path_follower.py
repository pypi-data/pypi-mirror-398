# pylint: disable=protected-access

import time
from typing import Union, cast

from ..ivention.exception import PathFollowingException
from ..ivention.iactuator import IActuator
from ..ivention.idigital_output import IDigitalOutput
from ..ivention.ipath_follower import IPathFollower, PathFollowerState
from ..ivention.types import path_follower_tool
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .actuator import Actuator
from .api import Api


class ModifiedPathFollowerState(PathFollowerState):
    def __init__(self, controller_id: str, api: Api) -> None:
        super().__init__()
        self._api = api
        self._controller_id = controller_id

    @property
    def speed(self) -> float:
        return float(self._api.get_path_status(self._controller_id)["speed"])

    @property
    def acceleration(self) -> float:
        return float(self._api.get_path_status(self._controller_id)["acceleration"])

    @property
    def running(self) -> bool:
        return bool(self._api.get_path_status(self._controller_id)["running"])

    @property
    def line_number(self) -> int:
        return int(self._api.get_path_status(self._controller_id)["line"])

    @property
    def current_command(self) -> Union[str, None]:
        return self._api.get_path_status(self._controller_id)["command"]

    @property
    def error(self) -> Union[str, None]:
        return self._api.get_path_status(self._controller_id)["error"]


@inherit_docstrings
class PathFollower(IPathFollower):
    """Path Follower Representation"""

    def __init__(
        self,
        x_axis: Union[IActuator, None] = None,
        y_axis: Union[IActuator, None] = None,
        z_axis: Union[IActuator, None] = None,
    ) -> None:
        super().__init__(x_axis, y_axis, z_axis)
        self._api: Api = self._get_axis_api(x_axis, y_axis, z_axis)
        self._state: ModifiedPathFollowerState = ModifiedPathFollowerState(self._controller_id, self._api)
        self._set_mapping(x_axis, y_axis, z_axis)

    def _get_axis_api(
        self,
        x_axis: Union[IActuator, None],
        y_axis: Union[IActuator, None],
        z_axis: Union[IActuator, None],
    ) -> Api:
        for axis in [x_axis, y_axis, z_axis]:
            if axis:
                # Type assertion to inform mypy that axis is of type Actuator
                axis = cast(Actuator, axis)
                axis_api = axis._api
                break
        return axis_api

    def _set_mapping(
        self,
        x_axis: Union[IActuator, None],
        y_axis: Union[IActuator, None],
        z_axis: Union[IActuator, None],
    ) -> None:
        axis_mapping = {
            "X": x_axis.configuration.uuid if x_axis else None,
            "Y": y_axis.configuration.uuid if y_axis else None,
            "Z": z_axis.configuration.uuid if z_axis else None,
        }
        # Remove None values from the dictionary
        axis_mapping = {k: v for k, v in axis_mapping.items() if v is not None}
        self._api.set_path_axes_map(axis_mapping)

    def add_tool(
        self,
        tool_id: int,
        m3_output: IDigitalOutput,
        m4_output: Union[IDigitalOutput, None] = None,
    ) -> None:
        tool: path_follower_tool.PathFollowerTool = {
            "cw": {
                "uuid": m3_output.configuration.uuid,
                "value": m3_output.configuration.active_high,
            },
        }
        if m4_output:
            tool["ccw"] = {
                "uuid": m4_output.configuration.uuid,
                "value": m4_output.configuration.active_high,
            }

        if not self._api.add_path_tool(tool_id, tool):
            raise PathFollowingException(f"Failed to add tool to pathfollower with tool id: {tool_id}")

    def start_path(self, gcode: str) -> None:
        wait_for_path_completion = True
        if not self._api.start_path(gcode, self._controller_id, wait_for_path_completion):
            raise PathFollowingException(
                f"""
                Failed to run start_path from pathFollower
                instance on controller: {self._controller_id}
                """
            )

    def start_path_async(self, gcode: str) -> None:
        wait_for_path_completion = False
        if not self._api.start_path(gcode, self._controller_id, wait_for_path_completion):
            raise PathFollowingException(
                f"""
                Failed to run start_path_async from pathFollower
                instance on controller: {self._controller_id}
                """
            )

    def stop_path(self) -> None:
        if not self._api.stop_path(self._controller_id):
            raise PathFollowingException(f"Failed to stop pathfollower path on controller: {self._controller_id} ")

    def wait_for_path_completion(self) -> None:
        while True:
            state = self.state
            if state.error is not None:
                raise PathFollowingException(state.error)
            if not state.running:
                break
            time.sleep(0.5)
