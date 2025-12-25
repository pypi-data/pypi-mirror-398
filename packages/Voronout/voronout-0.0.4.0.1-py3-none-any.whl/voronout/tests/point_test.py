from ..Point import Point

import json
import numpy as np

testPoint = Point(x = 0.3, y = 0.4)
testOtherPoint = Point(x = -0.1, y = 0.2)

def test_distance():
    distance = Point.distance(p1 = testPoint, p2 = testOtherPoint)
    # distance = sqrt((x2 - x1)^2 + (y2 - y1)^2)
    assert distance == 0.4472

def test_midpoint():
    midpoint = Point.midpoint(p1 = testPoint, p2 = testOtherPoint)

    # midpoint = ((x1 + x2)/2, (y1 + y2)/2)
    assert midpoint.x == 0.1
    assert midpoint.y == 0.3

def test_to_json():
    testPointJson = json.loads(repr(testPoint))

    assert len(testPointJson.keys()) == 2

    assert testPointJson["x"] == testPoint.x
    assert testPointJson["y"] == testPoint.y

def test_convert_point_base():
    pointBaseConverted = testPoint.convertPointBase()

    assert pointBaseConverted.x == testPoint.x
    assert pointBaseConverted.y == 1 - testPoint.y

def test_scale():
    widthScalar = 10
    heightScalar = 10

    pointScaled = testPoint.scale(widthScalar = widthScalar, heightScalar = heightScalar)
    assert pointScaled.x == testPoint.x * widthScalar
    assert pointScaled.y == testPoint.y * heightScalar

def test_to_array():
    npArray = np.array(testPoint)
    expectedNpArray = np.array(tuple((testPoint.x, testPoint.y)))
                               
    np.testing.assert_array_equal(npArray, expectedNpArray)