from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# from machinelogic.decorators.undocumented import undocumented
# for whatever reason, linter breaks up imports.
from ..ivention.types.robot_types import CartesianPose


class ICameraConfiguration(ABC):
    """
    A representation of the configuration of a Camera instance.
    This configuration defines what your Camera is and how it
    should behave when action is requested from it.
    """

    def __init__(
        self,
        uuid: str,
        name: str,
    ) -> None:
        self.__name = name
        self.__uuid = uuid

    def __str__(self) -> str:
        """The string representation of the camera configuration."""
        return f"Camera name: {self.name}, uuid: {self.uuid}"

    @property
    def name(self) -> str:
        """The friendly name of the camera."""
        return self.__name

    @property
    def uuid(self) -> str:
        """The camera's ID."""
        return self.__uuid


class ICamera(ABC):
    """
    A software representation of a camera. It is not recommended that you construct this
    object yourself. Rather, you should query it from a Machine instance:

    E.g.:
        machine = Machine()
        camera = machine.get_camera()

    """

    def __init__(self, configuration: ICameraConfiguration) -> None:
        self._configuration = configuration

    @abstractmethod
    def start(self) -> dict[str, Any] | str:
        """
        Start the camera pipeline, this initiate the capture of frames from the camera and thus uses some cpu/memory.

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation.  The dictionary has the following keys:
                        - 'serial' : serial number of the camera that was started
        """

    @abstractmethod
    def grab(self) -> dict[str, Any] | str:
        """
        grab a set of images (infra red left, right, color, depth...) and keep available for further commands.

        Returns:
            dict: [str, Any]
            A dictionary containing the result of the operation. The dictionary has the following keys:
                - 'timestamp'    : timestamps of the frameset
                - 'frame_number' : frame number from camera
                - 'filename'     : bag filename (if recording is enabled)
                - 'imageUrl1'    : infrared image #1 (left imager) url to retrieve a png
                - 'imageUrl2'    : infrared image #2 (right imager) url to retrieve a png
        """

    @abstractmethod
    def stop(self) -> dict[str, Any] | str:
        """
        Stop the camera pipeline, releasing cpu and memory.

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
                - 'serial' : serial number of the camera that was started
        """

    @abstractmethod
    def calibrate(self) -> dict[str, Any] | str:
        """
        Once enough calibration_pose() have been accumulated, this command will perform the Camera <-> Robot calibration.

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
                - 'valid' : the calibration was successful true/false
                - 'camera2gripper' : an homogeneous matrix containing the transformation R | T
                - 'rmsdall_mm' : rmsd error for all points and all poses
                - 'nbPoints' : total number of points used for calibration
                - 'nbPoses' : total number of poses used for calibration
        """

    @abstractmethod
    def calibration_save(self) -> str:
        """
        If the calibrate() command yields accurate results, the calibration_save() command will store this
        calibration on the storage for subsequent uses. This calibration will persist until a new
        calibration_save is executed or the calibration is reset.

        Returns:
            str: the yaml file representing the calibration
            on error: an empty string

        """

    @abstractmethod
    def calibration_pose(self, cartesian_pose: CartesianPose) -> dict[str, Any] | str:
        """
        This method will:
            - find the calibration target position in the image
            - calculate the camera position with respect to the calibration target
            - accumulate this pose with the cartesian_pose of the robot for the calibration
        Args:
            cartesian_pose (CartesianPose): cartesian robot pose obtained from robot.state.cartesian_position_data

        Returns:
            dict[str, Any]:
            A dictionary containing the result of the operation. The dictionary has the following keys:
                        - 'validDetection' : true/false, the detection grabbed by /grab was valid
                        - 'validTCPPose' : true/false, the extracted camera position was valid
                        - 'valid' : true/false, overall results of the poses is valid
                        - 'message' : error message
                        - 'timestamp' : timestamp of the images used
                        - 'timestampDomain' : timestamp domain of the images
                        - 'rmsd_mm' : rmsd error of the pose
                        - 'angle_rad' : angle in radian of the Z camera axis with respect to the charuco plane
                        - 'poseId' : the current poseId
                        - 'posesCount' : the number of poses accumuluted so far
                        - 'url1' : url of the infra1 (left imager) decorated image
                        - 'url2' : url of the infra2 (right imager) decorated image

        """

    @abstractmethod
    def calibration_reset(self, new_calibration_file: str = "") -> dict[str, Any] | str:
        """
        Revert the active calibration to its initial state. The calibration will be reset to empty,
        allowing for a fresh start.  If a calibration filename is specified, this calibration will be loaded after
        the reset.

        Args:
            new_calibration_file (str, optional): optional yaml filename to load a new calibration after reset

        Returns:
            dict[str, Any]:
            A dictionary containing the result of the operation. The dictionary has the following keys:
                        - 'reset'  : true/false the reset results
                        - 'reloaded': true/false the filename specified was loaded as a fresh calibration
                        - 'poseId' : the current poseId

        """

    @abstractmethod
    def _play(self, filename: str) -> dict[str, Any] | str:
        """
        Internal method used to grab images from a video file instead of a camera.
        It specifies a ROS bag file as the source of the video frames, replacing the camera with a video file.
        This is utilized in testing to ensure there are no regressions.
        This command must be issued before the command start()

        Args:
            filename (str): ros bag filename containing necessay images

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
            - 'filename' : if filename was present and useable, it is returned here
        """

    @abstractmethod
    def _record(self) -> dict[str, Any] | str:
        """
        This internal command will save every set of frames capture with grab in a ros bag file.  This command
        must be issued before start()

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
               - 'directory' : directory where the bag file is saved
               - 'bag_files' : full path of the bag filename
        """

    @abstractmethod
    def target_get_position(self, actual_tcp_pose: CartesianPose | None = None) -> dict[str, Any] | str:
        """
        The previously grabbed frames will be used to find a positionning target in the robot frame using
        the active calibration.

        Args:
            actual_tcp_pose (CartesianPose, optional): cartesian robot pose obtained from robot.state.cartesian_position_data

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
            -  'valid' : true/false, overall results of the poses is valid
            -  'calibration_valid' : true/false, the current calibration is valid
            -  'posInfra1_pixel' : x/y pixel position in the left image of the tag center
            -  'posInfra2_pixel' : x/y pixel position in the right image of the tag center
            -  'pointPosition_CameraFrame_m' : x/y/z position of the tag center in the camera frame
            -  'actualTCPPose' :  provided robot position
            -  'pointPos_RobotFrame_m' : x/y/z position of the tag center in the robot frame
            -  'delta_RobotFrame_m' : delta position to center the tag in the camera, in the robot frame

        """

    @abstractmethod
    def versions(self) -> dict[str, Any] | str:
        """return the calibration server's various versions

        Returns:
            dict[str, Any] | str:
            A dictionary containing the result of the operation. The dictionary has the following keys:
            -  'version' : The calibration server version
            -  'git' : The Git commit hash
            -  'OpenCV' : OpenCV version
            -  'Eigen' : Eigen library version
            -  'Realsense' : realsense library version
            -  'httplib' : httplib library version
            -  'gflags' : gflags library version

        """
