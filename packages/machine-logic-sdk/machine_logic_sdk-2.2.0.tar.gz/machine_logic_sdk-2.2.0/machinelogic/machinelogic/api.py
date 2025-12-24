# pylint: disable=too-many-lines
# mypy: disable-error-code="return-value, attr-defined"
import warnings
from dataclasses import asdict
from enum import Enum
from types import TracebackType
from typing import Any, Dict, List, Literal, Optional, Tuple, TypedDict, Union, cast

import requests
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import ConnectionPool
from urllib3.response import BaseHTTPResponse
from urllib3.util.retry import Retry

from machinelogic.ivention.types.batch_move import BatchMove
from machinelogic.ivention.types.robot_tcp import IncomingActiveTCP

from ..ivention.machine_configuration import (
    MachineConfiguration,
    parse_machine_configuration,
)
from ..ivention.types import (
    ac_motor_details,
    actuator_details,
    input_details,
    output_details,
    path_follower_status,
    path_follower_tool,
    pneumatic_details,
    robot_calibration,
    robot_types,
    scene_assets,
)


class ApiException(Exception):
    """Thrown by the system when we encounter an error during a request"""


class EndstopStateDict(TypedDict):
    """Dictionary representing the endstop state"""

    home: bool
    end: bool


class Routes(Enum):
    """
    Enum containing the list of routes supported by the execution engine.
    """

    RESET_CONTROLLER_OPERATIONAL_STATE = "/v1/python/reset_controller_operational_state"
    CONFIGURATION = "/v1/python/configuration"
    AXIS_CONFIGURATION = "/v1/python/configuration/axis"
    INPUT_CONFIGURATION = "/v1/python/configuration/input"
    OUTPUT_CONFIGURATION = "/v1/python/configuration/output"
    PNEUMATIC_CONFIGURATION = "/v1/python/configuration/pneumatic"
    AC_MOTOR_CONFIGURATION = "/v1/python/configuration/ac_motor"
    SMART_DRIVE_STATUS = "/v1/python/get_smartdrive_status"
    GET_SPEED = "/v1/python/get_speed"
    GET_MAX_SPEED = "/v1/python/get_max_speed"
    GET_ACCELERATION = "/v1/python/get_acceleration"
    MOVE_RELATIVE = "/v1/python/move_relative"
    MOVE_TO_POSITION = "/v1/python/move_to_position"
    HOME = "/v1/python/home"
    STOP_ACTUATOR_MOTION = "/v1/python/stop_actuator_motion"
    STOP_ACTUATOR_MOTION_COMBINED = "/v1/python/stop_actuator_motion_combined"
    SET_CONTINUOUS_MOVE = "/v1/python/set_continuous_move"
    STOP_CONTINUOUS_MOVE = "/v1/python/stop_continuous_move"
    GET_AXIS_POSITION = "/v1/python/axis_position"
    GET_AXIS_ACTUAL_TORQUE = "/v1/python/get_actual_torque"
    GET_INPUT = "/v1/python/io/input"
    IS_AXIS_MOTION_COMPLETE = "/v1/python/is_axis_motion_complete"
    GET_ENDSTOP_STATE_FOR_AXIS = "/v1/python/get_endstop_state_for_axis"
    WRITE_OUTPUT = "/v1/python/io/output"
    WAIT_FOR_MOTION_COMPLETION = "/v1/python/wait_for_motion_completion"
    PNEUMATIC_IDLE = "/v1/python/pneumatic/idle"
    PNEUMATIC_PUSH = "/v1/python/pneumatic/push"
    PNEUMATIC_PULL = "/v1/python/pneumatic/pull"
    MOVE_TO_POSITION_COMBINED = "/v1/python/move_to_position_combined"
    MOVE_RELATIVE_COMBINED = "/v1/python/move_relative_combined"
    HOME_ALL = "/v1/python/home_all"
    SET_AXES_POSITIONS = "/v1/python/set_axes_positions"
    STOP_ALL_MOTION = "/v1/python/stop_all_motion"
    MOVE_AC_MOTOR = "/v1/python/move_ac_motor"
    STOP_AC_MOTOR = "/v1/python/stop_ac_motor"
    BATCH_MOVE = "/v1/python/batch_move"

    # PATH FOLLOWING
    START_PATH = "/v1/python/path"
    STOP_PATH = "/v1/python/path/stop"
    GET_PATH_STATUS = "/v1/python/path/status"
    ADD_PATH_TOOL = "/v1/python/path/add_tool"
    SET_PATH_AXIS_MAP = "/v1/python/path/set_axis_map"

    # VISION
    VISION_CAMERA_CALIBRATION_SAVE = "/v1/vision/camera/calibration/save"
    VISION_CAMERA_CALIBRATE = "/v1/vision/camera/calibrate"
    VISION_CAMERA_START = "/v1/vision/camera/start"
    VISION_CAMERA_STOP = "/v1/vision/camera/stop"
    VISION_CAMERA_GRAB = "/v1/vision/camera/grab"
    VISION_CAMERA_RESET = "/v1/vision/camera/calibration/reset"
    VISION_CAMERA_PLAY = "/v1/vision/camera/play"
    VISION_CAMERA_RECORD = "/v1/vision/camera/record"
    VISION_CAMERA_TARGET = "/v1/vision/camera/target"
    VISION_CAMERA_POSE = "/v1/vision/camera/pose"
    VISION_VERSION = "/v1/vision/version"

    # ROBOT
    SET_TCP_OFFSET = "/v1/python/set_tcp_offset"
    RECONNECT_ROBOT = "/v1/python/robot/request_reconnect"
    SET_ACTIVE_TCP = "/v1/python/set_active_tcp"
    GET_ACTIVE_TCP = "/v1/python/get_active_tcp"

    # SCENE
    SCENE_ASSETS = "/v2/library/assets"
    SCENE_CALIBRATION_FRAMES = "/v1/robotCalibrations"


DEFAULT_TIMEOUT_SECONDS = 10
MOVEMENT_TIMEOUT_SECONDS = 300


class LoggingRetry(Retry):
    def increment(
        self,
        method: Optional[str] = None,
        url: Optional[str] = None,
        response: Optional[BaseHTTPResponse] = None,
        error: Optional[Exception] = None,
        _pool: Optional[ConnectionPool] = None,
        _stacktrace: Optional[TracebackType] = None,
    ) -> "LoggingRetry":
        current_attempt = len(self.history) + 1
        print(f"Retrying... (attempt {current_attempt}) for URL: {url}")
        return super().increment(
            method=method,
            url=url,
            response=response,
            error=error,
            _pool=_pool,
            _stacktrace=_stacktrace,
        )


def get_request_with_retries() -> requests.Session:
    """
    Create a requests.Session with retry logic.

    Returns:
        requests.Session: A session configured with retries.
    """
    retry_strategy = LoggingRetry(
        total=5,  # Total number of retries
        backoff_factor=1,  # Wait 1s, 2s, 4s, etc. between retries
        status_forcelist=[502, 503, 504],  # Retry on these HTTP statuses
        allowed_methods=["GET", "POST", "PUT"],  # Retry only these methods
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


class Api:
    """Interface between Python and the execution engine"""

    def __init__(self, conn_str: str):
        """
        Args:
            conn_str(str): The rest server that we will be sending requests to.
            _request(requests.Session): The request session that we will be using to send requests with retries.
        """
        self._conn_str = conn_str
        self._request = get_request_with_retries()

    def _make_route(self, route: Routes, params: str = "") -> str:
        return self._conn_str + str(route.value) + ("/" + params if params else "")

    def reset_controller_operational_state(self) -> bool:
        """Reset the controller operational state.

        Returns:
            bool: True if the drive errors were cleared, otherwise False
        """
        response = self._request.get(
            self._make_route(Routes.RESET_CONTROLLER_OPERATIONAL_STATE),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def get_machine_configuration(self) -> MachineConfiguration:
        """
        Fetches the machine configuration from the api and returns it in json format.

        Raises:
            ApiException: If we cannot get the machine config from the api, or if the machine config is malformed.

        Returns:
            Any: The machine configuration in JSON format.
        """
        response = self._request.get(
            self._make_route(Routes.CONFIGURATION),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        if not response.ok:
            raise ApiException(f"Failed to fetch the machine configuration: {str(response)}")

        return parse_machine_configuration(response.json())

    def get_scene_assets(
        self,
    ) -> Dict[Literal["assets"], List[scene_assets.SceneAssets]]:
        """Fetches the scene assets from the api and returns it in json format.

        Raises:
            ApiException: If we cannot get the scene assets

        Returns:
            Dict[Literal['assets'], List[scene_assets.SceneAssets]]: The scene assets in JSON format
        """
        response = self._request.get(
            self._make_route(Routes.SCENE_ASSETS),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        if not response.ok:
            raise ApiException(f"Failed to fetch the scene assets: {str(response)}")

        return cast(Dict[Literal["assets"], List[scene_assets.SceneAssets]], response.json())

    def get_calibration_frame(
        self, robot_calibration_uuid: str
    ) -> Dict[
        Literal["robotCalibration"],
        Union[robot_calibration.RobotCalibrationWithID, None],
    ]:
        """Fetches the calibration frame by uuid

        Args:
            robot_calibration_uuid (str): uuid of the calibration frame

        Raises:
            ApiException: If we cannot fetch the calibration frames

        Returns:
            Dict[Literal['robotCalibration'], Union[robot_calibration.RobotCalibrationWithID, None]]: {robotCalibration: calibration} where calibration is the set calibration
        """
        response = self._request.get(
            self._make_route(Routes.SCENE_CALIBRATION_FRAMES, robot_calibration_uuid),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        if not response.ok:
            raise ApiException(f"Failed to fetch the calibration frame: {str(response)}")
        return cast(
            Dict[
                Literal["robotCalibration"],
                Union[robot_calibration.RobotCalibrationWithID, None],
            ],
            response.json(),
        )

    def set_calibration_frame(
        self,
        robot_calibration_uuid: str,
        robot_calibration_values: robot_calibration.RobotCalibration,
    ) -> Dict[Literal["robotCalibration"], robot_calibration.RobotCalibrationWithID]:
        """Sets the calibration frame

        Args:
            robot_calibration_uuid (str): id of the robot calibration
            robot_calibration_values (robot_calibration.RobotCalibration): robot calibrated values

        Returns:
            Dict[Literal['robotCalibration'], robot_calibration.RobotCalibrationWithID]: calibration frame in JSON format
        """
        data = {"robotCalibration": robot_calibration_values}
        response = self._request.put(
            self._make_route(Routes.SCENE_CALIBRATION_FRAMES, robot_calibration_uuid),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Failed to set the calibration frame: {str(response)}")
        return cast(
            Dict[Literal["robotCalibration"], robot_calibration.RobotCalibrationWithID],
            response.ok,
        )

    def get_actuator_details(self, axis_uuid: str) -> actuator_details.ActuatorDetails:
        """Retrieve the details about an axis.

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            AxisDetails: Details of the axis
        Raises:
            VentionException: When we fail to query the details
        """
        params = {"axisUuid": axis_uuid}
        response = self._request.get(
            self._make_route(Routes.AXIS_CONFIGURATION),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to get details for axis with uuid: {axis_uuid}")
        return cast(actuator_details.ActuatorDetails, response.json())

    def get_input_details(self, input_uuid: str) -> input_details.DigitalInputDetails:
        """Retrieve the details about an input.

        Args:
            input_uuid (str): ID of the input

        Returns:
            DigitalInputDetails: Details of the input
        Raises:
            VentionException: When we fail to query the details
        """
        params = {"inputUuid": input_uuid}
        response = self._request.get(
            self._make_route(Routes.INPUT_CONFIGURATION),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to get details for input with uuid: {input_uuid}")
        return cast(input_details.DigitalInputDetails, response.json())

    def get_output_details(self, output_uuid: str) -> output_details.OutputDetails:
        """Retrieve the details about an output.

        Args:
            axis_uuid (str): ID of the output

        Returns:
            OutputDetails: Details of the output
        Raises:
            VentionException: When we fail to query the details
        """
        params = {"outputUuid": output_uuid}
        response = self._request.get(
            self._make_route(Routes.OUTPUT_CONFIGURATION),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to get details for output with uuid: {output_uuid}")
        return cast(output_details.OutputDetails, response.json())

    def get_pneumatic_details(self, pneumatic_uuid: str) -> pneumatic_details.PneumaticDetails:
        """Retrieve the details about a pneumatic.

        Args:
            pneumatic_uuid (str): ID of the pneumatic

        Returns:
            PneumaticDetails: Details of the pneumatic
        Raises:
            VentionException: When we fail to query the details
        """
        params = {"pneumaticUuid": pneumatic_uuid}
        response = self._request.get(
            self._make_route(Routes.PNEUMATIC_CONFIGURATION),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to get details for pneumatic with uuid: {pneumatic_uuid}")
        return cast(pneumatic_details.PneumaticDetails, response.json())

    def get_ac_motor_details(self, pneumatic_uuid: str) -> ac_motor_details.ACMotorDetails:
        """Retrieve the details about an AC Motor with VFD.

        Args:
            pneumatic_uuid (str): ID of the AC Motor

        Returns:
            ACMotorDetails: Details of the AC Motor
        Raises:
            VentionException: When we fail to query the details
        """
        params = {"pneumaticUuid": pneumatic_uuid}
        response = self._request.get(
            self._make_route(Routes.AC_MOTOR_CONFIGURATION),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to get details for ac_motor with uuid: {pneumatic_uuid}")
        return cast(ac_motor_details.ACMotorDetails, response.json())

    def get_speed(self, axis_uuid: str) -> float:
        """Retrieve the speed of an axis

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            float: Current speed of the axis
        """
        params = {"axisUuid": axis_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_SPEED),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return float(response_dict["speed"])
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_speed, no speed value was received from the server. Got: {response_dict}"
            ) from err

    def get_max_speed(self, axis_uuid: str) -> float:
        """Retrieve the max speed of an axis

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            float: Current speed of the axis
        """
        params = {"axisUuid": axis_uuid}
        try:
            response = self._request.get(
                self._make_route(Routes.GET_MAX_SPEED),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return float(response_dict["maxSpeed"])
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_max_speed, no max speed value was received from the server. Got: {response_dict}"
            ) from err

    def get_acceleration(self, axis_uuid: str) -> float:
        """Retrieve the acceleration of the axis

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            float: Current acceleration
        """
        params = {"axisUuid": axis_uuid}
        try:
            response = self._request.get(
                self._make_route(Routes.GET_ACCELERATION),
                params=params,
                timeout=MOVEMENT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return float(response_dict["acceleration"])
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_acceleration, no acceleration value was received from the server. Got: {response_dict}"
            ) from err

    def move_relative(
        self,
        axis_uuid: str,
        distance: float,
        wait_for_motion_completion: bool,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
        is_blind_move: bool = False,
    ) -> bool:
        """
        Args:
            axis_uuid (str): ID of the axis
            distance (float): Distance to move by
            timeout (float, optional): Timeout. Defaults to MOVEMENT_TIMEOUT_SECONDS.
            wait_for_motion_completion (bool, optional): If set True, we wait for the move to complete. Defaults to False.
            is_blind_move (bool, optional): Is blind move. Defaults to False.

        Returns:
            bool: True if we successfully moved
        """
        data = {
            "axisUuid": axis_uuid,
            "distance": distance,
            "waitForMotionCompletion": wait_for_motion_completion,
            "isBlindMove": is_blind_move,
        }
        response = self._request.post(
            self._make_route(Routes.MOVE_RELATIVE),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def move_absolute(
        self,
        axis_uuid: str,
        position: float,
        wait_for_motion_completion: bool,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
    ) -> bool:
        """
        Args:
            axis_uuid (str): ID of the axis
            position (float): Position to move to
            wait_for_motion_completion (bool): If set True, we wait for the move to complete

        Returns:
            bool: True if we moved succesfully
        """
        data = {
            "axisUuid": axis_uuid,
            "position": position,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.MOVE_TO_POSITION),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def home(
        self,
        axis_uuid: str,
        wait_for_motion_completion: bool,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
    ) -> bool:
        """Homes the axis

        Args:
            axis_uuid (str): ID of the axis
            wait_for_motion_completion (bool): If set True, we wait for the move to complete
            timeout (float, optional): Timeout. Defaults to MOVEMENT_TIMEOUT_SECONDS.

        Returns:
            bool: True if successful
        """
        data = {
            "axisUuid": axis_uuid,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(self._make_route(Routes.HOME), json=data, timeout=timeout)
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_motion(self, axis_uuid: str) -> bool:
        """Stop motion on a single axis

        Args:
            axis_uuid (str): ID of axis

        Returns:
            bool: True if motion on the axis was stopped, otherwise False
        """
        data = {"axisUuid": axis_uuid}
        response = self._request.post(
            self._make_route(Routes.STOP_ACTUATOR_MOTION),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_motion_combined(self, axis_uuid_list: list[str]) -> bool:
        """
        Stop motion on a list of axes.

        Args:
            axis_uuid (list): List of IDs of axes.

        Returns:
            bool: True if motion on the axes were stopped, otherwise False.
        """
        data = {"axisUuidList": axis_uuid_list}
        response = self._request.post(
            self._make_route(Routes.STOP_ACTUATOR_MOTION_COMBINED),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def set_continuous_move(
        self,
        axis_uuid: str,
        wait_for_motion_completion: bool,  # TODO: Support wait_for_motion_completion
        speed: Optional[float] = 100,
        acceleration: Optional[float] = 100,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
    ) -> bool:
        """Start a continuous move on the axis

        Args:
            axis_uuid (str): ID of the axis
            wait_for_motion_completion (bool): If set True, we wait for the move to complete
            speed (Optional[float], optional): Speed. Defaults to 100.
            acceleration (Optional[float], optional): Accelreation. Defaults to 100.
            timeout (int, optional): Timeout in seconds. Defaults to MOVEMENT_TIMEOUT_SECONDS.
        Returns:
            bool: True if successful, otherwise False
        """
        data = {
            "axisUuid": axis_uuid,
            "speed": speed,
            "acceleration": acceleration,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.SET_CONTINUOUS_MOVE),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_continuous_move(self, axis_uuid: str, acceleration: Optional[float] = 100) -> bool:
        """Stop continuous move on the axis

        Args:
            axis_uuid (str): ID of the axis
            acceleration (Optional[float], optional): Acceleration. Defaults to 100.

        Returns:
            bool: True if movement was stopped, otherwise False
        """
        data = {"axisUuid": axis_uuid, "acceleration": acceleration}
        response = self._request.post(
            self._make_route(Routes.STOP_CONTINUOUS_MOVE),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def get_axis_position(self, axis_uuid: str) -> float:
        """Retrieve the current position of the axis

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            float: Position of the axis
        """
        params = {"axisUuid": axis_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_AXIS_POSITION),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return float(response_dict["position"])
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_axis_position, no position value was received from the server. Got: {response_dict}"
            ) from err

    def read_input(self, input_uuid: str) -> int:
        """Retrieve the current value of the input.

        Args:
            input_uuid (str): ID of the input

        Raises:
            VentionException: If we are unable to read the input
            VentionException: If the response was malformed

        Returns:
            int: 1 or 0
        """
        params = {"inputUuid": input_uuid}
        response = self._request.get(
            self._make_route(Routes.GET_INPUT),
            params=params,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            raise ApiException(f"Unable to read input: {input_uuid}")

        response_dict = response.json()
        if "value" not in response_dict:
            raise ApiException(f"The 'value' key was not found in the response while reading input with uuid: {input_uuid}")
        return int(response_dict["value"])

    def get_axis_motion_completion(self, axis_uuid: str) -> bool:
        """Check if motion on the axis is completed

        Args:
            axis_uuid (str): ID of the axis

        Returns:
            bool: True if the axis is not in motion, otherwise False
        """
        params = {"axisUuid": axis_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.IS_AXIS_MOTION_COMPLETE),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return bool(response_dict["isComplete"])
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_axis_motion_completion, no completion value was received from the server. Got: {response_dict}"
            ) from err

    def get_endstop_state_for_axis(self, axis_uuid: str) -> EndstopStateDict:
        """_summary_

        Args:
            axisUuid (str): _description_

        Returns:
            EndstopStateDict: _description_
        """
        params = {"axisUuid": axis_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_ENDSTOP_STATE_FOR_AXIS),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return {"home": response_dict["home"], "end": response_dict["end"]}
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_endstop_state_for_axis, expected to receive home and end values, but got: {response_dict}"
            ) from err

    def write_output(self, output_uuid: str, value: Literal[1, 0]) -> bool:
        """Write a 1 or 0 to the output

        Args:
            output_uuid (str): ID of the output
            value (Literal[1, 0]): New value

        Returns:
            bool: True if successful, otherwise False
        """
        data = {"outputUuid": output_uuid, "value": value}
        response = self._request.post(
            self._make_route(Routes.WRITE_OUTPUT),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def wait_for_motion_completion(
        self,
        axis_uuid: Union[str, list[str]],
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Wait for motion completion on the provided axis.

        Args:
            axis_uuid (Union[str, list[str]], optional): Optional axis uuid to specifically wait on.
            timeout (Optional[float], optional): Optional timeout in seconds, defaults to eternity.

        Returns:
            bool: True if successful, otherwise False
        """
        data = {"axisUuidList": [axis_uuid] if isinstance(axis_uuid, str) else axis_uuid}
        response = self._request.get(
            self._make_route(Routes.WAIT_FOR_MOTION_COMPLETION),
            json=data,
            timeout=timeout,  # This can technically take an eternity to respond
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def pneumatic_idle(self, pneumatic_uuid: str) -> bool:
        """
        Idle the pneumatic with the provided uuid.

        Args:
            pneumatic_uuid (str): ID of the pneumatic of the actuator

        Returns:
            bool: True if the idle was successful, otherwise False.

        """
        data = {"pneumaticUuid": pneumatic_uuid}
        response = self._request.post(
            self._make_route(Routes.PNEUMATIC_IDLE),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def pneumatic_push(self, pneumatic_uuid: str, wait_for_motion_completion: bool) -> bool:
        """
        Push the pneumatic with the provided uuid.

        Args:
            pneumatic_uuid (str): ID of the pneumatic of the actuator
            wait_for_motion_completion (bool): If set to True, we wait for the push to complete, otherwise we fire and forget.

        Returns:
            bool: True if the push was successful, otherwise False.

        """
        data = {
            "pneumaticUuid": pneumatic_uuid,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.PNEUMATIC_PUSH),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def move_to_position_combined(
        self,
        move_to_position_payload_list: list[Tuple[str, float]],
        wait_for_motion_completion: bool,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
    ) -> bool:
        """
        Perform a combined move according to the provided tuple mapping from axis ID to position.

        Args:
            move_to_position_payload_list (list[Tuple[str, float]]): List of axis uuid and position pairs.
            wait_for_motion_completion (bool): When True, the request concludes when motion is completed, otherwise it completes after the request is confirmed.
            timeout (float, optional): Timeout. Defaults to MOVEMENT_TIMEOUT_SECONDS.

        Returns:
            bool: True if successful, otherwise False
        """
        payload_to_send = []
        for axis, position in move_to_position_payload_list:
            payload_to_send.append({"axis": axis, "position": position})
        data = {
            "moveToPositionPayloadList": payload_to_send,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.MOVE_TO_POSITION_COMBINED),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def pneumatic_pull(self, pneumatic_uuid: str, wait_for_motion_completion: bool) -> bool:
        """
        Push the pneumatic with the provided uuid.

        Args:
            pneumatic_uuid (str): ID of the pneumatic of the actuator
            wait_for_motion_completion (bool): If set to True, we wait for the pull to complete, otherwise we fire and forget.

        Returns:
            bool: True if the pull was successful, otherwise False.

        """
        data = {
            "pneumaticUuid": pneumatic_uuid,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.PNEUMATIC_PULL),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def move_relative_combined(
        self,
        move_relative_payload_list: list[Tuple[str, float]],
        wait_for_motion_completion: bool,
        timeout: float = MOVEMENT_TIMEOUT_SECONDS,
    ) -> bool:
        """
        Perform a combined move according to the provided tuple mapping from axis ID to distance moved.

        Args:
            move_to_position_payload_list (list[Tuple[str, float]]): List of axis uuid and position pairs.
            wait_for_motion_completion (bool): When True, the request concludes when motion is completed, otherwise it completes after the request is confirmed.
            timeout (float, optional): Timeout. Defaults to MOVEMENT_TIMEOUT_SECONDS.

        Returns:
            bool: True if successful, otherwise False
        """
        payload_to_send = []
        for axis, distance in move_relative_payload_list:
            payload_to_send.append({"axis": axis, "distance": distance})
        data = {
            "moveRelativePayloadList": payload_to_send,
            "waitForMotionCompletion": wait_for_motion_completion,
        }
        response = self._request.post(
            self._make_route(Routes.MOVE_RELATIVE_COMBINED),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def home_all(self, axis_uuid_list: list[str]) -> bool:
        """
        Move the axis provided in the list to home in the order specified in the list.

        Args:
            axis_uuid_list (list[str]): List of axes to home

        Returns:
            bool: True if homing was successful on all axes, otherwise False
        """
        data = {"axisUuidList": axis_uuid_list}
        response = self._request.post(
            self._make_route(Routes.HOME_ALL),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def set_axes_positions(self, axis_uuid_and_position_list: list[Tuple[str, float]]) -> bool:
        """
        Override the current position of each axis with the new positions.

        Args:
            axis_uuid_and_position_list (list[Tuple[str, float]): List of typles that map axis uuid to the new position

        Returns:
            bool: True if the axes positions were set successfully, otherwise False

        Raises:
            VentionException: If we fail to set the axes positions
        """
        payload = []
        for axis_uuid, position in axis_uuid_and_position_list:
            payload.append({"axisUuid": axis_uuid, "position": position})

        response = self._request.post(
            self._make_route(Routes.SET_AXES_POSITIONS),
            json={"axisUuidAndPositionList": payload},
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

        if not response.ok:
            error = response.json()
            raise ApiException(f"Failed to set_axes_positions: {error['error']}")

        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_all_motion(self) -> bool:
        """
        Stop all motion across every controller.

        Returns:
            bool: True if the stop was successful, otherwise False
        """
        response = self._request.post(self._make_route(Routes.STOP_ALL_MOTION), timeout=DEFAULT_TIMEOUT_SECONDS)
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def move_ac_motor(self, pneumatic_uuid: str, direction: Literal["forward", "reverse"]) -> bool:
        """
        Moves the AC motor with the provided uuid in the provided direction.

        Args:
            pneumaticUuid (str): ID of the AC motor
            direction (Literal["forward", "reverse"]): Direction to move in

        Returns:
            bool: True if the move was successful, otherwise False.

        """
        data = {
            "pneumaticUuid": pneumatic_uuid,
            "direction": direction,
        }
        response = self._request.post(
            self._make_route(Routes.MOVE_AC_MOTOR),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_ac_motor(self, pneumatic_uuid: str) -> bool:
        """
        Stops the AC motor with the provided uuid.

        Args:
            pneumaticUuid (str): ID of the AC motor
        Returns:
            bool: True if the stop was successful, otherwise False.

        """
        data = {"pneumaticUuid": pneumatic_uuid}
        response = self._request.post(
            self._make_route(Routes.STOP_AC_MOTOR),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def batch_move(self, moves: BatchMove) -> bool:
        """
        Move one or multiple axes in a single call. Supports TrapezoidalMoves, ContinuousMoves, and TorqueMoves.

        Args:
            moves (BatchMove): List of moves to perform.

        Returns:
            bool: True if the move was successful, otherwise False.
        """
        data = asdict(moves)
        response = self._request.post(
            self._make_route(Routes.BATCH_MOVE),
            json=data,
            timeout=MOVEMENT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def set_tcp_offset(self, robot_uuid: str, tcp_offset: robot_types.CartesianPose) -> bool:
        """
        Sets the Tool Center Point (TCP) offset for a specified robot.

        Args:
            robot_uuid (str): The unique identifier of the robot whose TCP offset is to be set.
            tcp_offset (CartesianPose): An object representing the desired TCP offset, including position and orientation.

        Returns:
            bool: True if the API call was successful and the TCP offset was set.
        """
        data = {
            "robotUuid": robot_uuid,
            "tcpOffset": tcp_offset,
        }
        response = self._request.post(
            self._make_route(Routes.SET_TCP_OFFSET),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def set_active_tcp(self, robot_uuid: str, tcp_uuid: str) -> bool:
        """
        Sets the active Tool Center Point (TCP) for a specified robot.

        Args:
            robot_uuid (str): The unique identifier of the robot whose active TCP is to be set.
            tcp_uuid (str): The unique identifier of the TCP to be set as active.
        Returns:
            bool: True if the API call was successful and the active TCP was set.
        """
        data = {
            "robotUuid": robot_uuid,
            "tcpUuid": tcp_uuid,
        }
        response = self._request.post(
            self._make_route(Routes.SET_ACTIVE_TCP),
            json=data,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def get_active_tcp(self, robot_uuid: str) -> IncomingActiveTCP:
        """
        Gets the active Tool Center Point (TCP) for a specified robot.

        Args:
            robot_uuid (str): The unique identifier of the robot whose active TCP is to be fetched.
        Returns:
            IncomingRequestedActiveTCP: The active TCP object.
        """
        params = {"robotUuid": robot_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_ACTIVE_TCP),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict = response.json()
            return cast(IncomingActiveTCP, response_dict)
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_active_tcp, no tcpUuid value was received from the server. Got: {response_dict}"
            ) from err

    def reconnect_robot(self, robot_uuid: str, timeout: Union[float, None]) -> bool:
        """
        Reconnects the robot with the provided uuid.

        Args:
            robot_uuid (str): ID of the robot
            timeout (Union[float, None], optional): Timeout.

        Returns:
            bool: True if the robot was reconnected, otherwise False.
        """
        data = {"robotUuid": robot_uuid}
        response = self._request.post(
            self._make_route(Routes.RECONNECT_ROBOT),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def get_axis_actual_torque(self, axis_uuid: str) -> dict[str, float]:
        """
        Get actual torque of the axis.

        Args:
            axis_uuid (str): ID of the axis.

        Returns:
            dict[str, float]: The torque of the axis.
        """
        params = {"axisUuid": axis_uuid}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_AXIS_ACTUAL_TORQUE),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict: dict[str, float] = response.json()
            return response_dict
        except KeyError as err:
            raise ApiException(
                f"Error while trying to get_axis_actual_torque, no completion value was received from the server. Got: {response_dict}"
            ) from err

    def start_path(self, gcode: str, controller_id: str, wait_on_path_completion: bool) -> bool:
        """Load and start a gcode path

        Args:
            gcode (str): G-code path to start
            controller_id (str): Id of the controller.
            waitForMotionComplete (bool, optional):
                If set True, we wait for the move to complete. Defaults to False.

        Returns:
            bool: True if we successfully ran G-code path
        """

        data = {
            "path": gcode,
            "acceleration": None,  # uses default from smart-drive server
            "speedOverride": None,  # uses default from smart-drive server
            "scaleMultiple": None,  # uses default from smart-drive server
            "dryRun": None,  # uses default from smart-drive server
            "controllerUuid": controller_id,
            "waitOnPathCompletion": wait_on_path_completion,
        }

        # if we have to wait on completion, we don't know how long it could take.
        timeout = None if wait_on_path_completion else DEFAULT_TIMEOUT_SECONDS

        response = self._request.post(
            self._make_route(Routes.START_PATH),
            json=data,
            timeout=timeout,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def stop_path(self, controller_id: str) -> dict[str, float]:
        """
        Stops the currently running path

        Args:
            controller_id (str): ID of the controller.

        Returns:
            bool: True if we successfully stop G-code path
        """
        params = {"controllerUuid": controller_id}

        try:
            response = self._request.get(
                self._make_route(Routes.STOP_PATH),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response_dict: dict[str, float] = response.json()
            return response_dict
        except KeyError as err:
            raise ApiException(
                f"""
                Error while trying to stop path,
                no completion value was received from the server. Got: {response_dict}
                """
            ) from err

    def get_path_status(self, controller_id: str) -> path_follower_status.PathFollowerStatus:
        """Get the status of the current path"

        Args:
            controller_id (str): Id of controller

        Returns:
            PathStatusPayload: Payload describing the status of the path
        """
        params = {"controllerUuid": controller_id}

        try:
            response = self._request.get(
                self._make_route(Routes.GET_PATH_STATUS),
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )

            response_dict = response.json()
            return cast(path_follower_status.PathFollowerStatus, response_dict["status"])
        except KeyError as err:
            raise ApiException(
                f"""
                Error while trying to get path status with
                controller id {controller_id}. Got: {response_dict}"""
            ) from err

    def add_path_tool(self, tool_id: int, tool: path_follower_tool.PathFollowerTool) -> bool:
        """Set a tool ID to a tool payload

        Args:
            tool_id (int): tool number
            tool (path_follower_tool.PathFollowerTool): {cw | ccw : {uuid: string, value: number}}

        Returns: bool: True if we successfully set tool
        """
        payload = {"toolId": tool_id, "tool": tool}

        response = self._request.post(
            self._make_route(Routes.ADD_PATH_TOOL),
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def set_path_axes_map(
        self,
        axis_map: Dict[str, Union[str, None]],
    ) -> bool:
        """Set the axis / drive association

        Args:
            axis_map (Dict[str, str]): A map with at least of the X|Y|Z keys to drive UUIDs

        Returns:
            bool: True if we successfully set the axis map
        """
        payload = {"axisMap": axis_map}

        response = self._request.post(
            self._make_route(Routes.SET_PATH_AXIS_MAP),
            json=payload,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if not response.ok:
            warnings.warn(response.text)
        return response.ok

    def _camera_action(self, route: Routes, params: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], str]:
        """
        Perform an action with the camera capture pipeline.

        Args:
            route: the url(Routes) to access the execution-engine's api
            params (Optional[Dict[str, Any]], optional): url parameters. Defaults to None.

        Raises:
            ApiException: Error during http get to vision server, the status is not 200
            ApiException: Error No completion value received from the server

        Returns:
            Union[Dict[str, Any], str]: json conversion results from http request
            str: when the action is not returning a parsed json, but a text payload.
        """

        try:
            response = self._request.get(self._make_route(route), timeout=DEFAULT_TIMEOUT_SECONDS, params=params)

            if not response.ok:
                raise ApiException(
                    f"Error during camera action: reponse from the server {self._conn_str} is: {response.status_code} text is: {response.text}"
                )
            data: Union[Dict[str, Any], str] = {}
            if "application/json" in response.headers.get("Content-Type", ""):
                try:
                    data = response.json()
                except ValueError:
                    data = response.text
            else:
                data = response.text

            return data  # This will return either a JSON object or a string.

        except KeyError as err:
            raise ApiException(f"Error during camera action: No completion value received from the server. Got: {response.text}") from err
        except ApiException as err:
            raise err
        except Exception as err:
            raise ApiException(f"An error occurred during camera action: {err}") from err

    def camera_start(self) -> Union[Dict[str, Any], str]:
        """
        Start the camera pipeline, this initiate the capture of frames from the camera.

        Returns:
            Union[Dict[str, Any], str]: dict of information:
                ['serial'] : serial number of the camera that was started
        """
        return self._camera_action(Routes.VISION_CAMERA_START)

    def camera_grab(self) -> Union[Dict[str, Any], str]:
        """
        If camera is started, grab a set of frames and keep in memory.

        Returns: dict of information:
                ['timestamp'] : timestamps of the frameset
                ['frame_number'] : frame number from camera
                ['filename'] : bag filename if recroding is enabled
                ['imageUrl1'] : infrared image #1 url to retrieve a png
                ['imageUrl2'] : infrared image #2 url to retrieve a png
        """
        grab_info = self._camera_action(Routes.VISION_CAMERA_GRAB)
        return grab_info

    def camera_stop(self) -> Union[Dict[str, Any], str]:
        """
        Stop the camera pipeline.

        Returns: dict of information:
                ['serial'] : serial number of the camera that was started
        """
        return self._camera_action(Routes.VISION_CAMERA_STOP)

    def camera_calibrate(self) -> Union[Dict[str, Any], str]:
        """
        perform the calibration hand-eye.

        Returns: dict of information:
                ['valid'] : the calibration was successful true/false
                ['camera2gripper'] : transformation R | T
                ['rmsdall_mm'] : rmsd error for all points and all poses
                ['nbPoints'] : total number of points used for calibration
                ['nbPoses'] : total number of poses used for calibration
        """
        return self._camera_action(Routes.VISION_CAMERA_CALIBRATE)

    def camera_calibration_save(self) -> str:
        """
        save the calibration to disk, it will be reused on all following re-boot.

        Returns: string containing the yaml file of the calibration
        """
        data: Union[Dict[str, Any], str] = self._camera_action(Routes.VISION_CAMERA_CALIBRATION_SAVE)
        if isinstance(data, str):
            return data
        return ""

    def camera_calibration_pose(self, actual_tcp_pose: robot_types.CartesianPose) -> Union[Dict[str, Any], str]:
        """
        This method adds a pose to the set of poses being accumulated to perform a calibration

        Args:
            actualTCPPose : array of 6 float values of the robot pose

        Returns: dict:
            ['validDetection'] : true/false, the detection grabbed by /grab was valid
            ['validTCPPose'] : true/false, the extracted camera position was valid
            ['valid'] : true/false, overall results of the poses is valid
            ['message'] : error message
            ['timestamp'] : timestamp of the images used
            ['timestampDomain'] : timestamp domain of the images
            ['rmsd_mm'] : rmsd error of the pose
            ['angle_rad'] : angle in radian of the Z camera axis with respect to the charuco plane
            ['poseId'] : the current poseId
            ['posesCount'] : the number of poses accumuluted so far
            ['url1'] : url of the infra1 decorated image
            ['url2'] : url of the infra2 decorated image
        """
        str_actual_tcp_pose = ",".join(str(number) for number in actual_tcp_pose)
        param = {"actualTCPPose": str_actual_tcp_pose}
        return self._camera_action(Routes.VISION_CAMERA_POSE, param)

    def camera_calibration_reset(self, new_calibration_file: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """
        This method is used to resets the internal calibration in memory to an empty state with no accumulated poses.

        Args:
            new_calibration_file : specify an optional yaml calibration filename to be used.

        Returns: dict:
            ['reset'] : true/false the reset results, success is true
            ['reloaded'] : true/false the filename specified was loaded as a fresh calibration
            ['poseId'] : the current poseId
        """
        param: Dict[str, Any] = {}
        if new_calibration_file is not None:
            param = {"filename": new_calibration_file}
        return self._camera_action(Routes.VISION_CAMERA_RESET, param)

    def camera_play(self, filename: str) -> Union[Dict[str, Any], str]:
        """
        specify a ros bag file to be used as a source of images instead of a camera.  This
        is mostly used internaly to run tests on the software packages.

        Returns: dict:
            ['filename'] : if filename was present and useable, it is returned here
        """
        param = {"filename": filename}
        return self._camera_action(Routes.VISION_CAMERA_PLAY, param)

    def camera_record(self) -> Union[Dict[str, Any], str]:
        """
        This method will indicate to the calibration server that every grabbed frames should be saved into
        a ros bag file. The ros bag filename will be saved in the yaml calibration file when calibration
        save is called.

        Returns: dict:
            ['bag_files'] : filename of the ros bag file containing the video images
        """
        return self._camera_action(Routes.VISION_CAMERA_RECORD)

    def camera_target_get_position(self, actual_tcp_pose: Optional[robot_types.CartesianPose] = None) -> Union[Dict[str, Any], str]:
        """
        This method is used to detect the position of a charuco target into the camera field of view.

        Args:
            actual_tcp_pose : array of 6 float values of the robot pose

        Returns: dict:

        On error:
            ['valid'] : false
        On success:
            ['valid'] : true
            ['calibration_valid'] : internal calibration is valid  true/false
            ['posInfra1_pixel'] : position of charuco tag in left imager
            ['posInfra2_pixel'] : positon of  charuco tag in right imager
            ['pointPosition_CameraFrame_m'] : x,y,z position of taget in camera frame
            ['actualTCPPose'] : parameter actual_tcp_pose is repeated on returned here, it is a way to validate parsing was done correctly;
            ['pointPos_RobotFrame_m'] : charuco target middle point in robot frame
            ['delta_RobotFrame_m'] : delta movement to have the charuco target in the center of the camera
            ['url1'] : http get url to retreive png image of the decorated left image
            ['url2'] : http get url to retreive png image of the decorated right image
        """
        param = {}
        if actual_tcp_pose is not None:
            str_actual_tcp_pose = ",".join(str(number) for number in actual_tcp_pose)
            param = {"actualTCPPose": str_actual_tcp_pose}
        return self._camera_action(Routes.VISION_CAMERA_TARGET, param)

    def camera_get_versions(self) -> Union[Dict[str, Any], str]:
        """
        get versions used by calibration server

        Returns: dict:
            ['version'] : vmvcal version
            ['git'] : The git commit hash of the calibration server build
            ['OpenCV'] : OpenCV version
            ['Eigen'] : Eigen library version
            ['Realsense'] : realsense library version
            ['httplib'] : httplib library version
            ['gflags'] : gflags library version
        """
        return self._camera_action(Routes.VISION_VERSION)

    def camera_service_present(self) -> bool:
        """
        dynamically detects if the camera service is present

        Returns: true: camera service is present
                 false: camera service is absent
        """
        try:
            # Query the calibration server for the presence of camera(s).  If no camera
            # is detected or the calibratrion server is not running, the camera api will not be active.
            # use the side effect of the exception generated when an http get timeout occurs
            self.camera_get_versions()
            return True
        except ApiException:
            pass
        return False
