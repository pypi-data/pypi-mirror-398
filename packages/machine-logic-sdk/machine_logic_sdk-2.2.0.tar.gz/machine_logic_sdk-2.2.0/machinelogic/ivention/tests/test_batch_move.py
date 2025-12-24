import unittest
from dataclasses import asdict

from machinelogic.ivention.types.batch_move import TrapezoidalMotion, TrapezoidalMove
from machinelogic.machinelogic.motion_profile import MotionProfile


class TestBatchMove(unittest.TestCase):
    def test_trapezoidal_move_asdict(self) -> None:
        motion_profile = MotionProfile(velocity=100.0, acceleration=50.0, jerk=10.0)
        trapezoidal_motion = TrapezoidalMotion(motor_address="motor_1", position_target=100.0)
        trapezoidal_move = TrapezoidalMove(
            motions=[trapezoidal_motion],
            use_relative_reference=True,
            motion_profile=motion_profile.strip_out_none_and_to_dict(),
            ignore_synchronization=False,
        )

        trapezoidal_move_dict = asdict(trapezoidal_move)
        self.assertEqual(trapezoidal_move_dict["motions"][0]["motor_address"], "motor_1")
        self.assertEqual(trapezoidal_move_dict["motions"][0]["position_target"], 100.0)
        self.assertTrue(trapezoidal_move_dict["use_relative_reference"])
        self.assertEqual(trapezoidal_move_dict["motion_profile"]["velocity"], 100.0)
        self.assertEqual(trapezoidal_move_dict["motion_profile"]["acceleration"], 50.0)
        self.assertEqual(trapezoidal_move_dict["motion_profile"]["jerk"], 10.0)
        self.assertFalse(trapezoidal_move_dict["ignore_synchronization"])
        self.assertEqual(trapezoidal_move_dict["move_type"], "TrapezoidalMove")


if __name__ == "__main__":
    unittest.main()
