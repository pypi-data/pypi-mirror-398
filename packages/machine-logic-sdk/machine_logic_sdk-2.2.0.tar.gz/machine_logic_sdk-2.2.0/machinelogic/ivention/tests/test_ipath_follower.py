# mypy: disable-error-code="attr-defined, var-annotated, no-untyped-def"
import unittest
from typing import Optional, TypedDict, Union

from machinelogic.ivention.exception import PathFollowingException
from machinelogic.ivention.ipath_follower import IPathFollower
from machinelogic.ivention.tests.test_imachine import DummyActuator

from ..idigital_output import IDigitalOutput


# define axisType
class AxisDict(TypedDict):
    axis_name: str
    controller_id: str


class DummyPathFollower(IPathFollower):
    def __init__(
        self,
        x_axis: Optional[AxisDict] = None,
        y_axis: Optional[AxisDict] = None,
        z_axis: Optional[AxisDict] = None,
    ):
        super().__init__(
            DummyActuator(x_axis["axis_name"], x_axis["controller_id"]) if x_axis else None,
            DummyActuator(y_axis["axis_name"], y_axis["controller_id"]) if y_axis else None,
            DummyActuator(z_axis["axis_name"], z_axis["controller_id"]) if z_axis else None,
        )

    def add_tool(
        self,
        tool_id: int,
        m3_output: IDigitalOutput,
        m4_output: Union[IDigitalOutput, None],
    ) -> None:
        raise NotImplementedError

    def start_path(self, gcode: str) -> None:
        raise NotImplementedError

    def start_path_async(self, gcode: str) -> None:
        raise NotImplementedError

    def stop_path(self) -> None:
        raise NotImplementedError

    def wait_for_path_completion(self) -> None:
        raise NotImplementedError


class TestIPathFollower(unittest.TestCase):
    def test_if_initialized_with_no_axes_then_raises_path_following_exception(self):
        with self.assertRaises(PathFollowingException) as path_following_exception:
            DummyPathFollower()
        self.assertEqual(
            "PathFollower object must contain at least one actuator",
            str(path_following_exception.exception),
        )

    def test_if_axes_on_different_machine_motions_then_raises_path_following_exception(
        self,
    ):
        with self.assertRaises(PathFollowingException) as path_following_exception:
            DummyPathFollower(
                {"axis_name": "xaxis", "controller_id": "1"},
                {"axis_name": "yaxis", "controller_id": "1"},
                {"axis_name": "zaxis", "controller_id": "2"},
            )
        self.assertEqual(
            "PathFollower Axes must be on the same controller",
            str(path_following_exception.exception),
        )

    def test_single_actuator_is_initialize(self):
        # Arrange
        axis_initializer: AxisDict = {"axis_name": "xaxis", "controller_id": "1"}
        path_follower = DummyPathFollower(axis_initializer)
        expected_x_axis = DummyActuator(axis_initializer["axis_name"], axis_initializer["controller_id"])
        expected_y_axis = None
        expected_z_axis = None

        # Assert
        if path_follower._x_axis is not None:
            self.assertEqual(
                path_follower._x_axis.configuration.name,
                expected_x_axis.configuration.name,
            )
            self.assertEqual(
                path_follower._x_axis.configuration.controller_id,
                expected_x_axis.configuration.controller_id,
            )
            self.assertEqual(path_follower._y_axis, expected_y_axis)
            self.assertEqual(path_follower._z_axis, expected_z_axis)
            self.assertFalse(path_follower.state.running)
            self.assertEqual(path_follower.state.line_number, 0)
            self.assertIsNone(path_follower.state.current_command)
            self.assertIsNone(path_follower.state.error)
            self.assertEqual(path_follower.state.speed, 0.0)
            self.assertEqual(path_follower.state.acceleration, 0.0)


if __name__ == "__main__":
    unittest.main()
