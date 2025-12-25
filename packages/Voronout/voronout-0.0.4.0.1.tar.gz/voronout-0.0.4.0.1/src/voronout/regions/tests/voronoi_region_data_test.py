from ..VoronoiRegionData import VoronoiRegionData

from uuid import uuid4

from ...edges.VoronoiEdgeData import VoronoiEdgeData
from ...edges.VoronoiEdge import VoronoiEdge

from ...Point import Point

# voronoi_diagram_test implicitly covers the success case.
def test_not_adding_edge_already_present():
    testRegionData = VoronoiRegionData(siteId = uuid4())

    testPoint0 = Point(x = 0.1, y = 0.1)
    testPoint1 = Point(x = 0.1, y = 0.2)

    testEdge = VoronoiEdge(vertex0Id = uuid4(), vertex1Id = uuid4(), neighborSiteId = uuid4())
    testEdgeData = VoronoiEdgeData(vertex0 = testPoint0, vertex1 = testPoint1, edgeInIds = testEdge)

    assert testRegionData.addEdgesData(edgeVertex0Index = 0, edgeVertex1Index = 1, neighborSiteIndex = 1, edgeData = testEdgeData)

    # Make sure that it covers both possible ways the edge could be described - A->B and B->A.
    assert not testRegionData.addEdgesData(edgeVertex0Index = 0, edgeVertex1Index = 1, neighborSiteIndex = 1, edgeData = testEdgeData)
    assert not testRegionData.addEdgesData(edgeVertex0Index = 1, edgeVertex1Index = 0, neighborSiteIndex = 1, edgeData = testEdgeData)