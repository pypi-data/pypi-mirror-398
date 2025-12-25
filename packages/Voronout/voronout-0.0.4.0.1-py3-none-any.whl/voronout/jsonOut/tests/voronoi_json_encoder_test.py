from ...Point import Point
from ...VoronoiDiagram import VoronoiDiagram

from ..VoronoiJSONEncoder import VoronoiJSONEncoder

# Derived from the default points at https://cfbrasz.github.io/Voronoi.html.
testPoints = tuple((Point(x = 0.5, y = 0.8667), Point(x = 0.1667, y = 0.7222), Point(x = 0.4444, y = 0.9000)))

def test_encoding_voronoi_diagram():
    voronoiDiagram = VoronoiDiagram(basePoints = testPoints, planeWidth = 600, planeHeight = 600)
    voronoiJsonEncoder = VoronoiJSONEncoder()

    voronoiJson = voronoiJsonEncoder.default(voronoiDiagram)

    # voronout/tests suites cover the correctness of data - this just verifies the JSON object's structure.
    voronoiJsonKeys = voronoiJson.keys()

    assert len(voronoiJsonKeys) == 3

    assert 'points' in voronoiJsonKeys
    assert 'vertices' in voronoiJsonKeys
    assert 'regions' in voronoiJsonKeys