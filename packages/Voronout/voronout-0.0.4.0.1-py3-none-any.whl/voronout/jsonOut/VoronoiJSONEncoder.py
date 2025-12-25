from json import JSONEncoder, loads as loadJSONString
from uuid import UUID

from ..Point import Point
from ..VoronoiDiagram import VoronoiDiagram

class VoronoiJSONEncoder(JSONEncoder):
    def _handlePointDict(self, pointDict: dict[UUID, Point]) -> dict[str, dict[str, float]]:
        return {str(key): loadJSONString(repr(value)) for (key, value) in pointDict.items()}
    
    def default(self, obj):
        if isinstance(obj, VoronoiDiagram):
            return {
                'points': self._handlePointDict(obj.points),
                'vertices': self._handlePointDict(obj.vertices),
                'regions': tuple((loadJSONString(repr(region)) for (_, region) in obj.voronoiRegions.items()))
            }
        else:
            return super().default(obj)