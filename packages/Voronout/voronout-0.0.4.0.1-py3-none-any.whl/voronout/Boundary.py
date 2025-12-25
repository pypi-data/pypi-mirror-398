from __future__ import annotations

from enum import Enum
from .Point import Point

from math import acos, degrees

from numpy import array as npArray, dot as npDotProduct

from .utils import boundValue

# _Quadrant is, on a line (p1, p2), with respect to an x/y graph with p1 at 0, 0
class _Quadrant(Enum):
    FIRST = 1 # dx > 0, dy > 0
    SECOND = 2 # dx < 0, dy > 0
    THIRD = 3 # dx < 0, dy < 0
    FOURTH = 4 # dx > 0, dy < 0

class Boundary(Enum):
    TOP = 1
    RIGHT = 2
    BOTTOM = 3
    LEFT = 4

    @staticmethod
    def _calculateLineSlope(linePoint1: Point, linePoint2: Point) -> float:
        return (linePoint2.y - linePoint1.y)/(linePoint2.x - linePoint1.x)

    # The boundary (line) a VoronoiDiagram edge might intersect with.
    @staticmethod
    def _getBoundaryLine(boundary: Boundary) -> tuple[Point]:
        match boundary:
            case Boundary.TOP: return tuple((Point(x = 0, y = 1), Point(x = 1, y = 1)))
            case Boundary.RIGHT: return tuple((Point(x = 1, y = 0), Point(x = 1, y = 1)))
            case Boundary.BOTTOM: return tuple((Point(x = 0, y = 0), Point(x = 1, y = 0)))
            case Boundary.LEFT: return tuple((Point(x = 0, y = 0), Point(x = 0, y = 1)))
    
    # quadrantVector approximates the relevant x/y-axis segment.
    @staticmethod
    def _getQuadrantVector(quadrant: _Quadrant, point: Point) -> npArray[float]:
        match quadrant:
            case _Quadrant.FIRST: return npArray((1, point.y))
            case _Quadrant.SECOND: return npArray((point.x, 1))
            case _Quadrant.THIRD: return npArray((-1, point.y))
            case _Quadrant.FOURTH: return npArray((point.x, -1))

    # Returns the next (counter-clockwise from quadrant) _Quadrant.
    @staticmethod
    def _determineNextQuadrant(quadrant: _Quadrant) -> _Quadrant:
        match quadrant:
            case _Quadrant.FIRST: return _Quadrant.SECOND
            case _Quadrant.SECOND: return _Quadrant.THIRD
            case _Quadrant.THIRD: return _Quadrant.FOURTH
            case _Quadrant.FOURTH: return _Quadrant.FIRST

    # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line#Line_defined_by_two_points
    @staticmethod
    def _pointDistanceToBoundary(point: Point, boundary: Boundary) -> float:
        (boundaryFirstPoint, boundarySecondPoint) = Boundary._getBoundaryLine(boundary)

        secondFirstDx = boundarySecondPoint.x - boundaryFirstPoint.x
        secondFirstDy = boundarySecondPoint.y - boundaryFirstPoint.y

        x2y1 = boundarySecondPoint.x * boundaryFirstPoint.y
        y2x1 = boundarySecondPoint.y * boundaryFirstPoint.x

        distanceNumerator = abs((secondFirstDy * point.x) - (secondFirstDx * point.y) + x2y1 - y2x1)
        distanceDenominator = Point.distance(p1 = boundaryFirstPoint, p2 = boundarySecondPoint)
                
        return distanceNumerator / distanceDenominator

    @staticmethod
    def _findClosestBoundaryToPoint(point: Point, boundaries: Boundary) -> Boundary:
        return sorted(boundaries, key = lambda boundary: Boundary._pointDistanceToBoundary(point = point, boundary = boundary))[0]

    # Like Point.distance(Point(vx, vy), Point(0, 0)), but I don't want to pass Point(0, 0).    
    @staticmethod
    def _calculateVectorMagnitude(vectorPoint: Point) -> float:
        return Point.distance(p1 = vectorPoint, p2 = Point(x = 0, y = 0))
    
    # Quadrants on an x/y graph are counterclockwise from east.
    @staticmethod
    def _determineVectorQuadrant(originatingPoint: Point, vectorPoint: Point) -> _Quadrant:
        dx = vectorPoint.x - originatingPoint.x
        dy = vectorPoint.y - originatingPoint.y

        if dx > 0 and dy > 0:
            return _Quadrant.FIRST
        elif dx < 0 and dy > 0:
            return _Quadrant.SECOND
        elif dx < 0 and dy < 0:
            return _Quadrant.THIRD
        else: # dx > 0 and dy < 0
            return _Quadrant.FOURTH
    
    # https://www.cuemath.com/geometry/angle-between-vectors/
    @staticmethod
    def _calculatePointQuadrantVectorsAngle(quadrantVectorPoint: Point, vectorPoint: Point, quadrant: _Quadrant) -> float:
        pointVector = npArray((vectorPoint.x, vectorPoint.y))
        quadrantVector = Boundary._getQuadrantVector(quadrant = quadrant, point = quadrantVectorPoint)

        vectorDotProduct = npDotProduct(pointVector, quadrantVector)
        
        pointMagnitude = Boundary._calculateVectorMagnitude(vectorPoint = vectorPoint)
        quadrantMagnitude = Boundary._calculateVectorMagnitude(vectorPoint = Point(x = quadrantVector[0], y = quadrantVector[1]))

        calculatedCos = vectorDotProduct / (pointMagnitude * quadrantMagnitude)

        # acos expects values in the range of [-1, 1]
        if calculatedCos > 0:
            return degrees(acos(min(calculatedCos, 1)))
        else:
            # calculatedCos <= 0
            return degrees(acos(max(calculatedCos, -1)))
    
    @staticmethod
    def findBoundaryInLineDirection(linePoint1: Point, linePoint2: Point) -> Boundary:
        lineQuadrant = Boundary._determineVectorQuadrant(originatingPoint = linePoint1, vectorPoint = linePoint2)
        nextQuadrant = Boundary._determineNextQuadrant(quadrant = lineQuadrant)

        lineQuadrantAngle = Boundary._calculatePointQuadrantVectorsAngle(quadrantVectorPoint = linePoint1, vectorPoint = linePoint2, quadrant = lineQuadrant)
        nextQuadrantAngle = Boundary._calculatePointQuadrantVectorsAngle(quadrantVectorPoint = linePoint1, vectorPoint = linePoint2, quadrant = nextQuadrant)

        match lineQuadrant:
            case _Quadrant.FIRST: return Boundary.RIGHT if lineQuadrantAngle < nextQuadrantAngle else Boundary.TOP
            case _Quadrant.SECOND: return Boundary.TOP if lineQuadrantAngle < nextQuadrantAngle else Boundary.LEFT
            case _Quadrant.THIRD: return Boundary.LEFT if lineQuadrantAngle < nextQuadrantAngle else Boundary.BOTTOM
            case _Quadrant.FOURTH: return Boundary.BOTTOM if lineQuadrantAngle < nextQuadrantAngle else Boundary.RIGHT
 
    @staticmethod
    # https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection#Given_two_points_on_each_line
    def boundaryLineIntersectionPoint(lineFirstPoint: Point, lineSecondPoint: Point, boundary: Boundary) -> Point:
        (boundaryFirstPoint, boundarySecondPoint) = Boundary._getBoundaryLine(boundary)

        x2dx1 = lineSecondPoint.x - lineFirstPoint.x
        y2dy1 = lineSecondPoint.y - lineFirstPoint.y

        # If line has a definite slope, we calculate intersection - if not, we just figure out which boundary it would vertically/horizontally intersect.
        if x2dx1 and y2dy1:
            x1y2 = lineFirstPoint.x * lineSecondPoint.y
            y1x2 = lineFirstPoint.y * lineSecondPoint.x

            x3dx4 = boundaryFirstPoint.x - boundarySecondPoint.x
            x1dx2 = -x2dx1

            x3y4 = boundaryFirstPoint.x * boundarySecondPoint.y
            y3x4 = boundaryFirstPoint.y * boundarySecondPoint.x

            y1dy2 = -y2dy1
            y3dy4 = boundaryFirstPoint.y - boundarySecondPoint.y

            pointDenominator = (x1dx2 * y3dy4) - (y1dy2 * x3dx4)

            pointXNumerator = ((x1y2 - y1x2) * x3dx4) - (x1dx2 * (x3y4 - y3x4))

            intersectionX = pointXNumerator / pointDenominator

            pointYNumerator = ((x1y2 - y1x2) * y3dy4) - (y1dy2 * (x3y4 - y3x4))

            intersectionY = pointYNumerator / pointDenominator

            intersectionPoint = Point(x = boundValue(value = intersectionX), y = boundValue(value = intersectionY))

            return intersectionPoint
        else:
            if x2dx1 and not y2dy1:
                # Lines with only dx will intersect either Left or Right boundaries.
                xCoord = 0 if lineSecondPoint.x < lineFirstPoint.x else 1
                xIntersectionPoint = Point(x = xCoord, y = lineSecondPoint.y)
                return xIntersectionPoint
            elif y2dy1 and not x2dx1:
                # Lines with only dy will intersect either Top or Bottom boundaries.
                yCoord = 0 if lineSecondPoint.y < lineFirstPoint.y else 1
                yIntersectionPoint = Point(x = lineSecondPoint.x, y = yCoord)
                return yIntersectionPoint
            else:
                # Lines without dx or dy shouldn't happen. 
                raise ValueError(f"Line {lineFirstPoint}, {lineSecondPoint} unexpectedly has both dx and dy = 0")
            
    @staticmethod
    def boundVertexOnX(vertex: Point, otherVertex: Point) -> Point:
        closestXBoundary = Boundary._findClosestBoundaryToPoint(point = vertex, boundaries = tuple((Boundary.LEFT, Boundary.RIGHT)))

        # xBound can only be Left or Right
        xBound = 0 if closestXBoundary == Boundary.LEFT else 1

        # Calculate (dy/dx) and dx..
        verticesSlope = Boundary._calculateLineSlope(linePoint1 = otherVertex, linePoint2 = vertex)
        boundDx = xBound - otherVertex.x

        # .. to do updatedY = otherVertex.y + dy.
        verticesSlopeDx = verticesSlope * boundDx
        updatedY = verticesSlopeDx + otherVertex.y

        boundedOnX = Point(x = boundValue(value = xBound), y = boundValue(value = updatedY))
        return boundedOnX
    
    @staticmethod
    def boundVertexOnY(vertex: Point, otherVertex: Point) -> Point:
        closestYBoundary = Boundary._findClosestBoundaryToPoint(point = vertex, boundaries = tuple((Boundary.BOTTOM, Boundary.TOP)))
        # yBound can only be Bottom or Top
        yBound = 0 if closestYBoundary == Boundary.BOTTOM else 1

        if vertex.x != otherVertex.x:
            # Calculate (dy/dx) and dy..
            verticesSlope = Boundary._calculateLineSlope(linePoint1 = otherVertex, linePoint2 = vertex)
            boundDy = yBound - otherVertex.y

            # .. to do updatedX = otherVertex.x + dx.
            verticesSlopeDy = boundDy/verticesSlope
            updatedX = verticesSlopeDy + otherVertex.x

            boundedOnY = Point(x = boundValue(value = updatedX), y = boundValue(value = yBound))
            return boundedOnY
        else:
            # We shouldn't calculate any slope if dx = 0.
            return Point(x = vertex.x, y = yBound)