from typing import Any

from machinelogic.ivention.iac_motor import ACMotorConfiguration
from machinelogic.ivention.iactuator import ActuatorConfiguration
from machinelogic.ivention.idigital_input import DigitalInputConfiguration
from machinelogic.ivention.idigital_output import DigitalOutputConfiguration
from machinelogic.ivention.imachine_motion import MachineMotionConfiguration
from machinelogic.ivention.ipneumatic import PneumaticConfiguration
from machinelogic.ivention.irobot import RobotConfiguration
from machinelogic.ivention.types.robot_tcp import IncomingRobotTCP, RobotTCP
from machinelogic.ivention.types.robot_types import CartesianPose


class MachineConfiguration:
    """
    A software representation of how the Machine is configured.
    A Machine is made up of many MachineMotions.
    """

    def __init__(self, machine_motion_configurations: list[MachineMotionConfiguration]) -> None:
        self.machine_motion_configurations: list[MachineMotionConfiguration] = machine_motion_configurations


def parse_machine_configuration(
    machine_configuration_json: Any,
) -> MachineConfiguration:
    """
    Parses a machine configuration from its JSON representation.

    Args:
        machine_configuration_json (Any): The machine configuration in JSON format.

    Returns:
        MachineConfiguration: The machine configuration object.
    """
    machine_configuration: MachineConfiguration = MachineConfiguration([])
    for controller_json in machine_configuration_json["controllerList"]:
        machine_motion_configuration = MachineMotionConfiguration(
            str(controller_json["uuid"]),
            str(controller_json["name"]),
            str(controller_json["mqttConnectionString"]),
        )

        machine_configuration.machine_motion_configurations.append(  # pylint: disable=protected-access
            machine_motion_configuration
        )

        robots_parameters_json = controller_json["robotsParametersList"]
        ros_address_json = controller_json["ventionRosAddress"]
        for robot_parameters in robots_parameters_json:
            machine_motion_configuration._robot_configuration_list.append(  # pylint: disable=protected-access
                _parse_robot_configuration(robot_parameters, ros_address_json)
            )

        axis_list_json = controller_json["axisList"]
        for axis_json in axis_list_json:
            machine_motion_configuration._actuator_configuration_list.append(  # pylint: disable=protected-access
                _parse_actuator_configuration(axis_json)
            )

        input_list_json = controller_json["inputList"]
        for input_json in input_list_json:
            machine_motion_configuration._input_configuration_list.append(  # pylint: disable=protected-access
                _parse_input_configuration(input_json)
            )

        output_list_json = controller_json["outputList"]
        for output_json in output_list_json:
            machine_motion_configuration._output_configuration_list.append(  # pylint: disable=protected-access
                _parse_output_configuration(output_json)
            )

        pneumatic_list_json = controller_json["pneumaticList"]
        for pneumatic_json in pneumatic_list_json:
            machine_motion_configuration._pneumatic_configuration_list.append(  # pylint: disable=protected-access
                _parse_pneumatic_configuration(pneumatic_json)
            )

        ac_motor_list_json = controller_json["acMotorList"]
        for ac_motor_json in ac_motor_list_json:
            machine_motion_configuration._ac_motor_configuration_list.append(  # pylint: disable=protected-access
                _parse_ac_motor_configuration(ac_motor_json)
            )

    return machine_configuration


def _parse_actuator_configuration(
    actuator_configuration_json: Any,
) -> ActuatorConfiguration:
    """
    Parses an actuator configuration from its JSON representation.

    Args:
        actuator_configuration_json (Any): The actuator configuration in JSON format.

    Returns:
        ActuatorConfiguration: The actuator configuration.
    """
    name = actuator_configuration_json["name"]
    uuid = actuator_configuration_json["uuid"]
    controller_id = actuator_configuration_json["controllerId"]
    parent_drive = actuator_configuration_json[  # pylint: disable=unused-variable
        "parentDrive"
    ]
    child_drives = actuator_configuration_json[  # pylint: disable=unused-variable
        "childDrives"
    ]
    mm_per_rotation = actuator_configuration_json[  # pylint: disable=unused-variable
        "mmPerRotation"
    ]
    actuator_type = actuator_configuration_json["axisType"]
    gear_ratio = actuator_configuration_json[  # pylint: disable=unused-variable
        "gearRatio"
    ]
    tuning_profile = actuator_configuration_json[  # pylint: disable=unused-variable
        "tuningProfile"
    ]
    rotation = actuator_configuration_json[  # pylint: disable=unused-variable
        "rotation"
    ]
    home_sensor = actuator_configuration_json["homeSensor"]
    units = actuator_configuration_json["units"]

    return ActuatorConfiguration(
        uuid,
        name,
        actuator_type,
        home_sensor,
        units,
        controller_id,
    )


def _parse_robot_configuration(robot_config_json: Any, ros_address: str) -> RobotConfiguration:
    name = robot_config_json["friendlyName"]
    uuid = robot_config_json["robotId"]
    robot_type = robot_config_json["robotType"]
    tcp_list = robot_config_json["tcpList"]

    return RobotConfiguration(
        ros_address=ros_address,
        uuid=uuid,
        name=name,
        robot_type=robot_type,
        tcp_list=_convert_incoming_robot_tcp_list_offset_object_to_list(tcp_list),
    )


def _convert_incoming_robot_tcp_list_offset_object_to_list(
    incoming_robot_tcp_list: list[IncomingRobotTCP],
) -> list[RobotTCP]:
    return [
        RobotTCP(
            name=incoming_robot_tcp["name"],
            uuid=incoming_robot_tcp["uuid"],
            tcp_offset=[
                incoming_robot_tcp["tcp_offset"]["x"],
                incoming_robot_tcp["tcp_offset"]["y"],
                incoming_robot_tcp["tcp_offset"]["z"],
                incoming_robot_tcp["tcp_offset"]["i"],
                incoming_robot_tcp["tcp_offset"]["j"],
                incoming_robot_tcp["tcp_offset"]["k"],
            ],
        )
        for incoming_robot_tcp in incoming_robot_tcp_list
    ]


def _parse_input_configuration(
    input_configuration_json: Any,
) -> DigitalInputConfiguration:
    """
    Parses an input configuration from its JSON representation.

    Args:
        input_configuration_json (Any): The input configuration in JSON format.

    Returns:
        DigitalInputConfiguration: The input configuration.
    """
    name = input_configuration_json["name"]
    uuid = input_configuration_json["uuid"]
    controller_id = input_configuration_json["controllerId"]
    pin = input_configuration_json["pin"]
    device_type = input_configuration_json[  # pylint: disable=unused-variable
        "deviceType"
    ]
    active_high = input_configuration_json["activeHigh"]
    control_module_address = input_configuration_json["controlModuleAddress"]
    device_id, controller_port = (
        control_module_address["deviceId"],
        control_module_address["devicePort"],
    )

    return DigitalInputConfiguration(
        uuid,
        name,
        device_id,
        controller_id,
        controller_port,
        pin,
        active_high,
    )


def _parse_output_configuration(
    output_configuration_json: Any,
) -> DigitalOutputConfiguration:
    """
    Parses an output configuration from its JSON representation.

    Args:
        output_configuration_json (Any): The output configuration in JSON format.

    Returns:
        DigitalOutputConfiguration: The output configuration.
    """
    name = output_configuration_json["name"]
    uuid = output_configuration_json["uuid"]
    controller_id = output_configuration_json["controllerId"]
    pin = output_configuration_json["pin"]
    device_type = output_configuration_json[  # pylint: disable=unused-variable
        "deviceType"
    ]
    active_high = output_configuration_json["activeHigh"]
    control_module_address = output_configuration_json["controlModuleAddress"]
    device_id, controller_port = (
        control_module_address["deviceId"],
        control_module_address["devicePort"],
    )

    return DigitalOutputConfiguration(
        uuid,
        name,
        device_id,
        controller_id,
        controller_port,
        pin,
        active_high,
    )


def _parse_pneumatic_configuration(
    pneumatic_configuration_json: Any,
) -> PneumaticConfiguration:
    """
    Parses a pneumatic configuration from its JSON representation.

    Args:
        pneumatic_configuration_json (Any): The pneumatic configuration in JSON format.

    Returns:
        PneumaticConfiguration: The pneumatic configuration.
    """
    name = pneumatic_configuration_json["name"]
    uuid = pneumatic_configuration_json["uuid"]
    controller_id = pneumatic_configuration_json["controllerId"]
    control_module_address = pneumatic_configuration_json["controlModuleAddress"]
    device_id, controller_port = (
        control_module_address["deviceId"],
        control_module_address["devicePort"],
    )
    output_pin_push = pneumatic_configuration_json["pushOutPin"]
    output_pin_pull = pneumatic_configuration_json["pullOutPin"]

    def _safe_get(key: str) -> Any:
        if key in pneumatic_configuration_json:
            return pneumatic_configuration_json[key]
        return None

    input_pin_push = _safe_get("pushInPin")
    input_pin_pull = _safe_get("pullInPin")

    return PneumaticConfiguration(
        uuid,
        name,
        controller_id,
        device_id,
        controller_port,
        output_pin_push,
        output_pin_pull,
        input_pin_push,
        input_pin_pull,
    )


def _parse_ac_motor_configuration(
    ac_motor_configuration_json: Any,
) -> ACMotorConfiguration:
    """
    Parses an AC motor configuration from its JSON representation.

    Args:
        ac_motor_configuration_json (Any): The AC motor configuration in JSON format.

    Returns:
        ACMotorConfiguration: The AC motor configuration.
    """
    name = ac_motor_configuration_json["name"]
    uuid = ac_motor_configuration_json["uuid"]
    controller_id = ac_motor_configuration_json["controllerId"]
    control_module_address = ac_motor_configuration_json["controlModuleAddress"]
    device_id, controller_port = (
        control_module_address["deviceId"],
        control_module_address["devicePort"],
    )
    output_pin_direction = ac_motor_configuration_json.get("directionOutPin", None)
    output_pin_move = ac_motor_configuration_json["moveOutPin"]

    return ACMotorConfiguration(
        uuid,
        name,
        controller_id,
        device_id,
        controller_port,
        output_pin_direction,
        output_pin_move,
    )
