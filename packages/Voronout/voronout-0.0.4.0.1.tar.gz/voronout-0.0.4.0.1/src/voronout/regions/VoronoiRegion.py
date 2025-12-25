from dataclasses import dataclass
from uuid import uuid4

from ..edges.VoronoiEdge import VoronoiEdge

@dataclass(frozen=True)
class VoronoiRegion:
    siteId: uuid4
    edges: tuple[VoronoiEdge]

    def neighbors(self) -> tuple[uuid4]:
        return tuple((edge.neighborSiteId for edge in self.edges))
    
    def __repr__(self) -> str:
        edges = ",".join(tuple(repr(edge) for edge in self.edges))
        return f'{{"siteId": "{str(self.siteId)}", "edges": [{edges}]}}'