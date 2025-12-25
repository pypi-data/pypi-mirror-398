from ..Point import Point

from ..VoronoiDiagram import VoronoiDiagram
from ..VoronoiDiagramToJSON import toJson

testOutputFile = "voronoi.json"

def test_voronoi_diagram_to_json(tmp_path):
    diagramPoints = tuple(
        (Point(x = .0556, y = .1333),
        Point(x = .1667, y = .2778),
        Point(x = .4444, y = .1000))
    )

    # Other tests check VoronoiDiagram correctness - we just need to verify that the file gets created.
    voronoiJsonPath = (tmp_path / testOutputFile)
    assert not voronoiJsonPath.exists()
    
    voronoiDiagram = VoronoiDiagram(basePoints = diagramPoints, planeWidth = 600, planeHeight = 600)
    toJson(voronoiDiagram = voronoiDiagram, voronoiJsonPath = voronoiJsonPath)

    assert voronoiJsonPath.exists()