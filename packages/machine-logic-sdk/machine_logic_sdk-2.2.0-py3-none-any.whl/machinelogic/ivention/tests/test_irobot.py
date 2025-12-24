import unittest

from machinelogic.ivention.irobot import IRobot


class TestRobotMethodsExist(unittest.TestCase):
    def test_on_log_alarm_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "on_log_alarm"))

    def test_move_stop_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "move_stop"))

    def test_compute_forward_kinematics_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "compute_forward_kinematics"))

    def test_compute_inverse_kinematics_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "compute_inverse_kinematics"))

    def test_set_tcp_offset_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "set_tcp_offset"))

    def test_set_tcp_offset_is_deprecated(self) -> None:
        self.assertTrue(
            getattr(IRobot.set_tcp_offset, "__deprecated__", False),
            "set_tcp_offset should be decorated with @deprecated",
        )

    def test_set_active_tcp_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "set_active_tcp"))

    def test_reset_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "reset"))

    def test_set_tool_digital_output_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "set_tool_digital_output"))

    def test_create_sequence_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "create_sequence"))

    def test_set_payload_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "set_payload"))

    def test_on_system_state_change_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "on_system_state_change"))

    def test_movej_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "movej"))

    def test_movel_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "movel"))

    def test_movej_async_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "movej_async"))

    def test_movel_async_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "movel_async"))

    def test_execute_sequence_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "execute_sequence"))

    def test_execute_sequence_async_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "execute_sequence_async"))

    def test_wait_for_motion_completion_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "wait_for_motion_completion"))

    def test_teach_mode_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "teach_mode"))

    def test_reconnect_exists(self) -> None:
        self.assertTrue(hasattr(IRobot, "reconnect"))


if __name__ == "__main__":
    unittest.main()
