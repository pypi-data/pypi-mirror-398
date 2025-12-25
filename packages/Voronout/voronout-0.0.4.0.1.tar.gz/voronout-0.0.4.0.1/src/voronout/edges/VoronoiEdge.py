from dataclasses import dataclass
from uuid import uuid4

@dataclass(frozen=True)
class VoronoiEdge:
    vertex0Id: uuid4
    vertex1Id: uuid4
    # The region neighboring the one this is contained in.
    neighborSiteId: uuid4

    def __repr__(self) -> str:
        return f'{{"vertex0Id": "{str(self.vertex0Id)}", "vertex1Id": "{str(self.vertex1Id)}", "neighborSiteId": "{str(self.neighborSiteId)}"}}'