from dataclasses import dataclass, field
from uuid import uuid4

from ..edges.VoronoiEdgeData import VoronoiEdgeData

@dataclass
class VoronoiRegionData:
    siteId: uuid4
    # A dict of edges such that iterating over it will make one complete loop around the region. .. str needs to be a key that can handle multiple [0, -1] cases
    _edgesData: dict[str, VoronoiEdgeData] = field(default_factory=dict)

    def _makeEdgeVerticesIdentifier(self, edgeVertex0Index: int, edgeVertex1Index: int, neighborSiteIndex: int) -> str:
        return f"{edgeVertex0Index}_{edgeVertex1Index}_{neighborSiteIndex}"
    
    def addEdgesData(self, edgeVertex0Index: int, edgeVertex1Index: int, neighborSiteIndex: int, edgeData: VoronoiEdgeData) -> bool:
        edgeVerticies01Identifier = self._makeEdgeVerticesIdentifier(edgeVertex0Index = edgeVertex0Index, edgeVertex1Index = edgeVertex1Index, neighborSiteIndex = neighborSiteIndex)
        edgeVerticies10Identifier = self._makeEdgeVerticesIdentifier(edgeVertex0Index = edgeVertex1Index, edgeVertex1Index = edgeVertex0Index, neighborSiteIndex = neighborSiteIndex)

        edgeDataAlreadyAdded = edgeVerticies01Identifier in self._edgesData or edgeVerticies10Identifier in self._edgesData
        if not edgeDataAlreadyAdded:
            # .. then it's OK to add self._edgesData[edgeVerticies01Identifier].
            self._edgesData[edgeVerticies01Identifier] = edgeData
            return True
        else:
            # .. then it's not OK to add self._edgesData[edgeVerticies01Identifier], and we should indicate that.
            return False

    def edges(self):
        for edgeData in self._edgesData.values():
            yield edgeData