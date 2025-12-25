from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np

from .utils import boundValue

@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def __init__(self, x, y):
        object.__setattr__(self, "x", boundValue(value = x))
        object.__setattr__(self, "y", boundValue(value = y))

    @staticmethod
    def distance(p1: Point, p2: Point) -> float:
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        return boundValue(value = sqrt(pow(dx, 2) + pow(dy, 2)))

    @staticmethod
    def midpoint(p1: Point, p2: Point) -> Point:
        midpointX = boundValue(value = (p1.x + p2.x)/2)
        midpointY = boundValue(value = (p1.y + p2.y)/2)

        return Point(x = midpointX, y = midpointY)
    
    # For converting between 0, 0 (top-left) and 0, 0 (bottom-left).
    def convertPointBase(self) -> Point:
        return Point(x = self.x, y = boundValue(value = 1 - self.y))
    
    # For scaling a Point up when outputting it.
    def scale(self, widthScalar: float, heightScalar: float) -> Point:
        return Point(x = boundValue(value = self.x * widthScalar), y = boundValue(value = self.y * heightScalar))
    
    # For ease of JSON conversion.
    def __repr__(self) -> str:
        # -0.0 and 0.0 are equivalent in Python - no reason for JSON output of both not to uniformly be 0.0.
        x = abs(self.x) if self.x == 0.0 else self.x
        y = abs(self.y) if self.y == 0.0 else self.y

        return f'{{"x": {x}, "y": {y}}}'
    
    # For using Point in scipy.spatial methods that take ArrayLike parameters.
    def __array__(self, dtype=None, copy=None):
        return np.array(tuple((self.x, self.y)))
    
    # For checking that Point is in a given list.
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y