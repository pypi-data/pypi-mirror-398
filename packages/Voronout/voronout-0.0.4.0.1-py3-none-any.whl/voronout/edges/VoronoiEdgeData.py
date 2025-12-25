from dataclasses import dataclass
from uuid import uuid4

from ..Point import Point
from .VoronoiEdge import VoronoiEdge

@dataclass(frozen=True)
class VoronoiEdgeData:
    vertex0: Point
    vertex1: Point

    edgeInIds: VoronoiEdge

    def vertex0Id(self) -> uuid4:
        return self.edgeInIds.vertex0Id
    
    def vertex1Id(self) -> uuid4:
        return self.edgeInIds.vertex1Id
    
    def neighborSiteId(self) -> uuid4:
        return self.edgeInIds.neighborSiteId