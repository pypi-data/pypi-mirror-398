# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import json
import math
import unittest

from ..angle import UnitOfAngle, convert_angle


class TestConvertAngle(unittest.TestCase):
    def test_degrees_to_radians(self) -> None:
        result = convert_angle(180, UnitOfAngle.DEGREE, UnitOfAngle.RADIANS)
        expected_value = math.pi
        self.assertAlmostEqual(result["value"], expected_value, places=5)
        self.assertEqual(result["unit"], UnitOfAngle.RADIANS)

    def test_radians_to_degrees(self) -> None:
        result = convert_angle(math.pi, UnitOfAngle.RADIANS, UnitOfAngle.DEGREE)
        expected_value = 180
        self.assertAlmostEqual(result["value"], expected_value, places=5)
        self.assertEqual(result["unit"], UnitOfAngle.DEGREE)

    def test_degrees_to_degrees(self) -> None:
        result = convert_angle(180, UnitOfAngle.DEGREE, UnitOfAngle.DEGREE)
        expected_value = 180
        self.assertAlmostEqual(result["value"], expected_value, places=5)
        self.assertEqual(result["unit"], UnitOfAngle.DEGREE)

    def test_radians_to_radians(self) -> None:
        result = convert_angle(math.pi, UnitOfAngle.RADIANS, UnitOfAngle.RADIANS)
        expected_value = math.pi
        self.assertAlmostEqual(result["value"], expected_value, places=5)
        self.assertEqual(result["unit"], UnitOfAngle.RADIANS)


class TestUnitOfAngleSerialization(unittest.TestCase):
    def test_serialization(self) -> None:
        # Test serialization of DEGREE
        degree = UnitOfAngle.DEGREE
        serialized_degree = json.dumps({"unit": degree})
        self.assertEqual(serialized_degree, '{"unit": "Degrees"}')

        # Test serialization of RADIANS
        radians = UnitOfAngle.RADIANS
        serialized_radians = json.dumps({"unit": radians})
        self.assertEqual(serialized_radians, '{"unit": "Radians"}')


# This allows running the tests when this script is executed

if __name__ == "__main__":
    unittest.main()
