# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import json
import unittest

from ..distance import Distance, UnitOfDistance, convert_distance


class TestConvertDistance(unittest.TestCase):
    def test_meters_to_millimeters(self) -> None:
        result = convert_distance(1, UnitOfDistance.METERS, UnitOfDistance.MILLIMETERS)
        expected = Distance(value=1000, unit=UnitOfDistance.MILLIMETERS)
        self.assertEqual(result, expected)

    def test_millimeters_to_meters(self) -> None:
        result = convert_distance(1000, UnitOfDistance.MILLIMETERS, UnitOfDistance.METERS)
        expected = Distance(value=1, unit=UnitOfDistance.METERS)
        self.assertEqual(result, expected)

    def test_meters_to_meters(self) -> None:
        result = convert_distance(1, UnitOfDistance.METERS, UnitOfDistance.METERS)
        expected = Distance(value=1, unit=UnitOfDistance.METERS)
        self.assertEqual(result, expected)

    def test_millimeters_to_millimeters(self) -> None:
        result = convert_distance(1000, UnitOfDistance.MILLIMETERS, UnitOfDistance.MILLIMETERS)
        expected = Distance(value=1000, unit=UnitOfDistance.MILLIMETERS)
        self.assertEqual(result, expected)


class TestUnitOfDistanceSerialization(unittest.TestCase):
    def test_serialization(self) -> None:
        # Test serialization of METERS
        meters = UnitOfDistance.METERS
        serialized_meters = json.dumps({"unit": meters})
        self.assertEqual(serialized_meters, '{"unit": "Meters"}')

        # Test serialization of MILLIMETERS
        millimeters = UnitOfDistance.MILLIMETERS
        serialized_millimeters = json.dumps({"unit": millimeters})
        self.assertEqual(serialized_millimeters, '{"unit": "Millimeters"}')


if __name__ == "__main__":
    unittest.main()
