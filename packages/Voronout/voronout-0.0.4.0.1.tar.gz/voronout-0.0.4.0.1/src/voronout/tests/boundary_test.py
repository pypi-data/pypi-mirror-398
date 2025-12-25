from ..Point import Point
from ..Boundary import Boundary

import pytest


def test_bound_vertex_on_x_left():
    testFirstPoint = Point(x = 0.3, y = 0.4)
    testSecondPoint = Point(x = -0.3, y = 0.4)
    boundedPoint = Boundary.boundVertexOnX(vertex = testFirstPoint, otherVertex = testSecondPoint)

    assert boundedPoint.x == 0
    assert boundedPoint.y == 0.4

def test_bound_vertex_on_x_right():
    testFirstPoint = Point(x = 0.7, y = 0.4)
    testSecondPoint = Point(x = 1.3, y = 0.4)
    boundedPoint = Boundary.boundVertexOnX(vertex = testFirstPoint, otherVertex = testSecondPoint)

    assert boundedPoint.x == 1
    assert boundedPoint.y == 0.4

def test_bound_vertex_on_y_top():
    testFirstPoint = Point(x = 0.3, y = 0.7)
    testSecondPoint = Point(x = 0.3, y = 1.3)
    boundedPoint = Boundary.boundVertexOnY(vertex = testFirstPoint, otherVertex = testSecondPoint)

    assert boundedPoint.x == 0.3
    assert boundedPoint.y == 1

def test_bound_vertex_on_y_bottom():
    testFirstPoint = Point(x = 0.3, y = 0.3)
    testSecondPoint = Point(x = 0.6, y = -0.3)
    boundedPoint = Boundary.boundVertexOnY(vertex = testFirstPoint, otherVertex = testSecondPoint)

    assert boundedPoint.x == 0.45
    assert boundedPoint.y == 0

def test_bound_vertex_on_y_bottom_dx_zero():
    testFirstPoint = Point(x = 0.3, y = 0.3)
    testSecondPoint = Point(x = 0.3, y = 0.6)
    boundedPoint = Boundary.boundVertexOnY(vertex = testFirstPoint, otherVertex = testSecondPoint)

    assert boundedPoint.x == 0.3
    assert boundedPoint.y == 0

findBoundaryTestData = [
    [Point(x = 0.6, y = 0.4), Boundary.RIGHT], # Quadrant 1, angle < 45 degrees (counter-clockwise from east)
    [Point(x = 0.4, y = 0.6), Boundary.TOP], # Quadrant 1, 45 degrees < angle < 90 degrees
    [Point(x = -0.4, y = 0.6), Boundary.TOP], # Quadrant 2, 90 degrees < angle < 135 degrees
    [Point(x = -0.6, y = 0.4), Boundary.LEFT], # Quadrant 2, 135 degrees < angle < 180 degrees
    [Point(x = -0.6, y = -0.4), Boundary.LEFT], # Quadrant 3, 180 degrees < angle < 225 degrees
    [Point(x = -0.4, y = -0.6), Boundary.BOTTOM], # Quadrant 3, 225 degrees < angle < 270 degres
    [Point(x = 0.4, y = -0.6), Boundary.BOTTOM], # Quadrant 4, 270 degrees < angle < 315 degrees
    [Point(x = 0.6, y = -0.4), Boundary.RIGHT] # Quadrant 4, 315 degrees < angle < 360 degrees
]

@pytest.mark.parametrize("linePoint, expectedBoundary", findBoundaryTestData)
def test_find_boundary_in_line_direction(linePoint: Point, expectedBoundary: Boundary):
    quadrantPoint = Point(x = 0, y = 0)
    assert Boundary.findBoundaryInLineDirection(linePoint1 = quadrantPoint, linePoint2 = linePoint) == expectedBoundary

def test_find_boundary_line_intersection_point():
    intersectionPoint = Boundary.boundaryLineIntersectionPoint(lineFirstPoint = Point(x = 0.3, y = 0.4), lineSecondPoint = Point(x = -0.1, y = 0), boundary = Boundary.LEFT)
    
    # (0.3, 0.4) -> (-0.1, 0) would intersect at (0, 0.1)
    assert intersectionPoint.x == 0
    assert intersectionPoint.y == 0.1