from typing import List, Union

import numpy
from typing_extensions import TypeAlias

Matrix: TypeAlias = numpy.ndarray[numpy.float64, numpy.dtype[numpy.float64]]
Degrees = float
Millimeters = float
JointAnglesDegrees = List[Degrees]  # float[6]: [degrees]
CartesianPose = List[Union[Degrees, Millimeters]]  # float[6]: [mm] + [degrees]
DegreesPerSecond = Union[List[float], float]  # angular velocity units.
DegreesPerSecondVector = List[float]  # list only.
DegreesPerSecondSquared = Union[List[float], float]  # angular acceleration units.
DegreesPerSecondSquaredVector = List[float]  # list only.
MillimetersPerSecond = float  # linear velocity units.
MillimetersPerSecondSquared = float  # linear accleration units.
ScaleFactor = float  # between 0.0 and 1.0
Kilograms = float
