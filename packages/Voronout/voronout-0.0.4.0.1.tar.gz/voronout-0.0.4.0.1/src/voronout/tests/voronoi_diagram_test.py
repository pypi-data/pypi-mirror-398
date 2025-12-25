from ..Point import Point
from ..VoronoiDiagram import VoronoiDiagram

from pytest import raises
from uuid import uuid4

planeWidth = 600
planeHeight = 600

# All sites (and expected values) calculated via https://cfbrasz.github.io/Voronoi.html (x = "50 150 400", y = "120 250 90")
siteOne = Point(x = 0.0556, y = 0.1333)
siteTwo = Point(x = 0.1667, y = 0.2778)
siteThree = Point(x = 0.4444, y = 0.1000)

scaledSiteOne = siteOne.scale(widthScalar = planeWidth, heightScalar = planeHeight)
scaledSiteTwo = siteTwo.scale(widthScalar = planeWidth, heightScalar = planeHeight)
scaledSiteThree = siteThree.scale(widthScalar = planeWidth, heightScalar = planeHeight)

planeWidth = 600
planeHeight = 600

# For each region in testPoints, the neighbors are the other points' regions.
sitesExpectedNeighbors = {
    scaledSiteOne: tuple((scaledSiteTwo, scaledSiteThree)),
    scaledSiteTwo: tuple((scaledSiteOne, scaledSiteThree)),
    scaledSiteThree: tuple((scaledSiteOne, scaledSiteTwo))
}

expectedDiagramVertex = Point(x = 149.16, y = 59.94)

expectedBoundaryVertex1 = Point(x = 0, y = 174.6)
expectedBoundaryVertex2 = Point(x = 144.12, y = 0)
expectedBoundaryVertex3 = Point(x = 494.46, y = 600)

def _idsByPoint(pointsById: dict[uuid4, Point]) -> dict[Point, uuid4]:
    return {point: pointId for (pointId, point) in pointsById.items()}

# Verifies that VoronoiDiagram is constructed as expected.
def test_voronoi_diagram():
    testPoints = tuple((siteOne, siteTwo, siteThree))
    voronoiDiagram = VoronoiDiagram(basePoints = testPoints, planeWidth = planeWidth, planeHeight = planeHeight)

    # We should have one diagram vertex and three boundary vertices.
    assert len(voronoiDiagram.vertices) == 4

    vertexValues = voronoiDiagram.vertices.values()

    assert expectedDiagramVertex in vertexValues
    assert expectedBoundaryVertex1 in vertexValues
    assert expectedBoundaryVertex2 in vertexValues
    assert expectedBoundaryVertex3 in vertexValues
    
    # Identifiers are randomly generated, so we need to dynamically get them.
    voronoiDiagramPointsIdMap = _idsByPoint(pointsById = voronoiDiagram.points)
    
    # Check that we only have the points we passed in..
    assert len(voronoiDiagramPointsIdMap) == len(testPoints)

    scaledTestPoints = tuple((scaledSiteOne, scaledSiteTwo, scaledSiteThree))

    # .. and then check the data in terms of each point.
    for testPoint in scaledTestPoints:
        testPointIdentifier = voronoiDiagramPointsIdMap[testPoint]
        testPointRegion = voronoiDiagram.voronoiRegions[testPointIdentifier]

        assert testPointRegion.siteId == testPointIdentifier
        
        testPointRegionNeighbors = set(testPointRegion.neighbors())

        testExpectedNeighbors = sitesExpectedNeighbors[testPoint]
        testExpectedIdentifiers = set((voronoiDiagramPointsIdMap[testExpectedNeighbor] for testExpectedNeighbor in testExpectedNeighbors))

        assert testPointRegionNeighbors == testExpectedIdentifiers

def test_voronoi_diagram_too_few_base_points():
    with raises(ValueError):
        VoronoiDiagram(basePoints = (siteOne, siteTwo), planeWidth = planeWidth, planeHeight = planeHeight)

def test_voronoi_diagram_base_points_outside_bounds():
    outOfBoundsSiteThree = Point(x = 0.4444, y = 1.1000)
    with raises(ValueError):
        VoronoiDiagram(basePoints = (siteOne, siteTwo, outOfBoundsSiteThree), planeWidth = planeWidth, planeHeight = planeHeight)