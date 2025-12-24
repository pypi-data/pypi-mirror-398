from typing import Literal

from machinelogic.ivention.exception import SceneException
from machinelogic.ivention.types.scene_assets import AssetList
from machinelogic.machinelogic.utils.compute_position_relative_to_base import (
    compute_position_relative_to_base,
)

from ..ivention.ireference_frame import IReferenceFrame, IReferenceFrameConfiguration
from ..ivention.types.robot_types import CartesianPose
from ..ivention.util.inheritance import inherit_docstrings  # type: ignore
from .api import Api


class ReferenceFrameConfiguration(IReferenceFrameConfiguration):
    def __init__(
        self,
        api: Api,
        uuid: str,
        name: str,
        default_position: CartesianPose,
        parent_reference_frame_id: str,
    ) -> None:
        super().__init__(uuid, name, default_position, parent_reference_frame_id)
        self._api = api


@inherit_docstrings
class ReferenceFrame(IReferenceFrame):
    """
    A software representation of a Reference Frame as defined within the scene assets pane.
    A reference frame is defined in mm and degrees, where the angles are extrinsic Euler
    angles in XYZ order.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
        default_position: CartesianPose,
        api: Api,
        parent_reference_frame_id: str,
    ) -> None:
        self.__configuration = ReferenceFrameConfiguration(api, uuid, name, default_position, parent_reference_frame_id)
        self._api = api
        self._assets: AssetList = []

    @property
    def _configuration(self) -> ReferenceFrameConfiguration:
        return self.__configuration

    def _set_asset_list(self, assets: AssetList) -> None:
        self._assets = assets

    def get_position(self, relative_to: Literal["robot_base", "parent"] = "parent") -> CartesianPose:
        if relative_to == "robot_base":
            return compute_position_relative_to_base(self, self._assets)
        elif relative_to == "parent":
            return self._configuration.default_position
        else:
            raise SceneException(f"Invalid relative_to value: {relative_to}, expected 'robot_base' or 'parent'.")
