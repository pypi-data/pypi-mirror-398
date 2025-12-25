from uuid import uuid4

from ..edges.VoronoiEdge import VoronoiEdge

import json

def test_to_json():
    identifier0 = uuid4()
    identifier1 = uuid4()
    neighborIdentifier = uuid4()

    voronoiEdge = VoronoiEdge(vertex0Id = identifier0, vertex1Id = identifier1, neighborSiteId = neighborIdentifier)
    voronoiEdgeJson = json.loads(repr(voronoiEdge))

    assert len(voronoiEdgeJson.keys()) == 3

    assert voronoiEdgeJson["vertex0Id"] == str(identifier0)
    assert voronoiEdgeJson["vertex1Id"] == str(identifier1)
    assert voronoiEdgeJson["neighborSiteId"] == str(neighborIdentifier)