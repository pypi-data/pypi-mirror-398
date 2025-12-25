from uuid import uuid4

from ..edges.VoronoiEdge import VoronoiEdge
from ..regions.VoronoiRegion import VoronoiRegion

import json

def _makeVoronoiEdge() -> VoronoiEdge:
    return VoronoiEdge(vertex0Id = uuid4(), vertex1Id = uuid4(), neighborSiteId = uuid4())

testVoronoiEdge = _makeVoronoiEdge()
testOtherVoronoiEdge = _makeVoronoiEdge()
testVoronoiRegion = VoronoiRegion(siteId = uuid4(), edges = tuple((testVoronoiEdge, testOtherVoronoiEdge)))

def test_neighbors():
    regionNeighbors = testVoronoiRegion.neighbors()
    assert tuple((testVoronoiEdge.neighborSiteId, testOtherVoronoiEdge.neighborSiteId)) == regionNeighbors

def test_to_json():
    regionJson = json.loads(repr(testVoronoiRegion))

    assert len(regionJson.keys()) == 2

    assert regionJson["siteId"] == str(testVoronoiRegion.siteId)
    assert regionJson["edges"] == [json.loads(repr(testVoronoiEdge)), json.loads(repr(testOtherVoronoiEdge))]