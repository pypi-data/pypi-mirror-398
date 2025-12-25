from scipy.spatial import voronoi_plot_2d

from voronout.VoronoiDiagram import VoronoiDiagram
from voronout.Point import Point 
from voronout.VoronoiDiagramToJSON import toJson
from matplotlib import pyplot

import random

# basePoints are percentages that we scale up later
# looks good now - just fix a few bugs - division by 0, lines crossing over, edge case with the above three points - clean up tests, and we are good

basePoints = tuple(
    (Point(x = 0.6473, y = 0.5131), 
     Point(x = 0.159, y = 0.1831), 
     Point(x = 0.9664, y = 0.664),
     Point(x = 0.558, y = 0.263)))
#basePoints = tuple((Point(x = random.random(), y = random.random()) for _ in range(15)))
print(tuple((repr(basePoint) for basePoint in basePoints)))

baseWidth = 600
baseHeight = 600

voronoiDiagram = VoronoiDiagram(basePoints = basePoints, planeWidth = baseWidth, planeHeight = baseHeight)

pyplot.ylim(bottom = baseWidth, top = 0)

for voronoiRegion in voronoiDiagram.voronoiRegions.values():
    for voronoiRegionEdge in voronoiRegion.edges:
        vertexIdentifier0 = voronoiRegionEdge.vertex0Id
        vertexIdentifier1 = voronoiRegionEdge.vertex1Id

        vertex0 = voronoiDiagram.vertices[vertexIdentifier0]
        vertex1 = voronoiDiagram.vertices[vertexIdentifier1]
        
        pyplot.plot([vertex0.x, vertex1.x], [vertex0.y, vertex1.y])
    
voronoi_plot_2d(voronoiDiagram._voronoiDiagram, show_points = True, show_vertices = True)
pyplot.show()

toJson(voronoiDiagram = voronoiDiagram, voronoiJsonPath = "voronoi.json")