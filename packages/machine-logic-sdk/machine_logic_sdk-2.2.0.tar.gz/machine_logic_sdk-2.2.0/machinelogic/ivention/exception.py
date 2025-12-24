"""
Module containing possible exceptions.
"""


class VentionException(Exception):
    """A general exception thrown via the Vention API.

    Args:
        Exception (Exception): Super class
    """

    def __init__(self, message: str):
        """
        Args:
            message (str): Description of error
        """
        super().__init__(message)


class MachineException(VentionException):
    """An exception thrown by the Machine

    Args:
        Exception (VentionException): Super class
    """


class MachineMotionException(VentionException):
    """An exeption thrown by a MachineMotion

    Args:
        VentionException (VentionException): Super class
    """


class ActuatorException(VentionException):
    """An exception thrown by an Actuator

    Args:
        VentionException (VentionException): Super class
    """


class RobotException(VentionException):
    """An exception thrown by a Robot

    Args:
        VentionException (VentionException): Super class
    """


class ActuatorGroupException(VentionException):
    """An exception thrown by an ActuatorGroup

    Args:
        VentionException (VentionException): Super class
    """


class DigitalInputException(VentionException):
    """An exception thrown by an INput

    Args:
        VentionException (VentionException): Super class
    """


class DigitalOutputException(VentionException):
    """An exception thrown by an Output

    Args:
        VentionException (VentionException): Super class
    """


class PneumaticException(VentionException):
    """An exception thrown by a Pneumatic

    Args:
        VentionException (_type_): Super class
    """


class ACMotorException(VentionException):
    """An exception thrown by a AC motor

    Args:
        VentionException(__type__): Super class
    """


class BagGripperException(VentionException):
    """An exception thrown by a BagGripper

    Args:
        VentionException(__type__): Super class
    """


class PathFollowingException(VentionException):
    """An exception thrown by a path following operation

    Args:
        VentionException(__type__): Super class
    """


class SceneException(VentionException):
    """An exception thrown by a scene Asset

    Args:
        VentionException(__type__): Super class
    """
