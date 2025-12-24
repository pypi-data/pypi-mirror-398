"""_summary_"""

from abc import ABC
from typing import Tuple, Union

from ..decorators.undocumented import undocumented
from .exception import MachineMotionException
from .iac_motor import ACMotorConfiguration, IACMotor
from .iactuator import ActuatorConfiguration, IActuator
from .icamera import ICamera
from .idigital_input import DigitalInputConfiguration, IDigitalInput
from .idigital_output import DigitalOutputConfiguration, IDigitalOutput
from .ipneumatic import IPneumatic, PneumaticConfiguration
from .irobot import IRobot, RobotConfiguration


class MachineMotionConfiguration:
    """
    A software representation of the configuration of a single MachineMotion
    instance as it was defined in the MachineLogic configuration page.
    """

    def __init__(self, uuid: str, name: str, mqtt_conn_str: str) -> None:
        """
        Args:
            name (str): Name of the MachineMotion
            uuid (str): Unique ID
        """
        self._uuid = uuid
        self._name = name
        self._mqtt_conn_str = mqtt_conn_str
        self._actuator_configuration_list: list[ActuatorConfiguration] = []
        self._robot_configuration_list: list[RobotConfiguration] = []
        self._input_configuration_list: list[DigitalInputConfiguration] = []
        self._output_configuration_list: list[DigitalOutputConfiguration] = []
        self._pneumatic_configuration_list: list[PneumaticConfiguration] = []
        self._ac_motor_configuration_list: list[ACMotorConfiguration] = []

    @property
    def name(self) -> str:
        """The name of the MachineMotion."""
        return self._name

    @property
    def uuid(self) -> str:
        """The ID of the MachineMotion."""
        return self._uuid

    @property
    def mqtt_conn_str(self) -> str:
        """The connection string for the MQTT client."""
        return self._mqtt_conn_str


class IMachineMotion(ABC):
    """
    A software representation of a MachineMotion controller. The MachineMotion
    is comprised of many actuators, inputs, outputs, pneumatics, and ac motors.
    It keeps a persistent connection to MQTT as well.

    You should NEVER construct this object yourself. Instead, it is best to rely
    on the Machine instance to provide you with a list of the available MachineMotions.
    """

    def __init__(self, configuration: MachineMotionConfiguration) -> None:
        self._configuration: MachineMotionConfiguration = configuration
        self._actuator_list: list[IActuator] = []
        self._robot_list: list[IRobot] = []
        self._input_list: list[IDigitalInput] = []
        self._output_list: list[IDigitalOutput] = []
        self._pneumatic_list: list[IPneumatic] = []
        self._ac_motor_list: list[IACMotor] = []
        self._camera_list: list[ICamera] = []

    @property
    def configuration(self) -> MachineMotionConfiguration:
        """
        MachineMotionConfiguration: The representation of the configuration associated with this MachineMotion.
        """
        return self._configuration

    @undocumented
    def get_actuator(self, name: str) -> IActuator:
        """
        Retrieves an Actuator by name.

        Args:
            name (str): Name of the Actuator.

        Returns:
            IActuator: The Actuator that was found.

        Raises:
            MachineMotionException: If it is not found
        """
        for actuator in self._actuator_list:
            if actuator.configuration.name == name:
                return actuator

        raise MachineMotionException(f"Failed to find Actuator with name: {name}")

    @undocumented
    def get_robot(self, name: Union[str, None] = None) -> IRobot:
        """
        Retrieve a robot by name. If no name is specified, then return the first robot.

        Args:
            name (str): Robot name. If it's `None` and there's a single robot in the list of robots, then the robot is returned.

        Returns:
            IRobot: Found robot

        Raises:
            MachineMotionException: If no robot is found (either wrong robot name or no robots are available)
        """
        if not self._robot_list:
            raise MachineMotionException("No robots found")

        if name is None and len(self._robot_list) == 1:
            return self._robot_list[0]

        for robot in self._robot_list:
            if robot.configuration.name == name:
                return robot

        raise MachineMotionException(f"Failed to find a robot with name: {name}")

    @undocumented
    def get_camera(self) -> ICamera:
        """
        Retrieve a camera if presents.

        Returns:
            ICamera: Found camera

        Raises:
            MachineMotionException: If no camera is found
        """
        if (not self._camera_list) or (len(self._camera_list) != 1):
            raise MachineMotionException("No cameras found")

        return self._camera_list[0]

    @undocumented
    def get_input(self, name: str) -> IDigitalInput:
        """
        Retrieves an DigitalInput by name.

        Args:
            name (str): The name of the DigitalInput.

        Returns:
            IDigitalInput: The DigitalInput that was found.

        Raises:
            MachineMotionException: If it is not found.
        """
        for inpt in self._input_list:
            if inpt.configuration.name == name:
                return inpt

        raise MachineMotionException(f"Failed to find DigitalInput with name: {name}")

    @undocumented
    def get_output(self, name: str) -> IDigitalOutput:
        """
        Retrieves an Output by name.

        Args:
            name (str): The name of the Output

        Returns:
            IOutput: The Output that was found.

        Raises:
            MachineMotionException: If it is not found.
        """
        for output in self._output_list:
            if output.configuration.name == name:
                return output

        raise MachineMotionException(f"Failed to find Output with name: {name}")

    @undocumented
    def get_pneumatic(self, name: str) -> IPneumatic:
        """
        Retrieves a Pneumatic by name.

        Args:
            name (str): The name of the Pneumatic.

        Returns:
            IPneumatic: The Pneumatic that was found.

        Raises:
            MachineMotionException: If it is not found.
        """
        for pneumatic in self._pneumatic_list:
            if pneumatic.configuration.name == name:
                return pneumatic

        raise MachineMotionException(f"Failed to find Pneumatic with name: {name}")

    @undocumented
    def get_ac_motor(self, name: str) -> IACMotor:
        """
        Retrieves an AC Motor by name.

        Args:
            name (str): The name of the AC Motor.

        Returns:
            IACMotor: The AC Motor that was found.

        Raises:
            MachineMotionException: If it is not found.
        """
        for ac_motor in self._ac_motor_list:
            if ac_motor.configuration.name == name:
                return ac_motor

        raise MachineMotionException(f"Failed to find AC motor with name: {name}")

    @undocumented
    def list_components(
        self,
    ) -> Tuple[
        list[IActuator],
        list[IRobot],
        list[IDigitalInput],
        list[IDigitalOutput],
        list[IPneumatic],
        list[IACMotor],
        list[ICamera],
    ]:
        """Retrieve a tuple containing the components of this MachineMotion

        Returns:
            Tuple[list[IActuator], list[IRobot], list[IDigitalInput], list[IOutput], list[IPneumatic], list[IACMotor], list[ICamera]]:
                Tuple containing actuators, robots, inputs, outputs, pneumatics, and AC motors.
        """
        return (
            self._actuator_list,
            self._robot_list,
            self._input_list,
            self._output_list,
            self._pneumatic_list,
            self._ac_motor_list,
            self._camera_list,
        )
