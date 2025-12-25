from json import dump as writeJsonOut

from .VoronoiDiagram import VoronoiDiagram
from .jsonOut.VoronoiJSONEncoder import VoronoiJSONEncoder

def toJson(voronoiDiagram: VoronoiDiagram, voronoiJsonPath: str):
    with open(voronoiJsonPath, "w") as jsonOut:
        writeJsonOut(obj = voronoiDiagram, fp = jsonOut, cls = VoronoiJSONEncoder)