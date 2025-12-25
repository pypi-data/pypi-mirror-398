# Voronout is..

.. a Python module that, given.. 

* a set of points on a 2D plane bounded by `0 <= x <= 1` and `0 <= y <= 1`
* the `planeWidth` and `planeHeight` to scale those points to  

..outputs JSON describing the Voronoi diagram in that 2D plan.

The Voronoi computation is [SciPy's](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Voronoi.html#scipy.spatial.Voronoi). Voronout translates that into more easily parsible JSON:

```
{
    "points": {.."<pointUUID>": {"x": <point.x>, "y": <point.y>}..},
    "vertices": {.."<vertexUUID>": {"x": <vertex.x>, "y": <vertex.y>}..},
    "regions": [
        ..
        {
            "siteIdentifier": "<pointUUID>",
            "edges": [
                ..
                {
                    "vertexIdentifier0": <vertexUUID0>,
                    "vertexIdentifier1": <vertexUUID1>,
                    "neighborSiteIdentifier": <pointUUID>
                }
                ..
            ]
        }
        ..
    ]
}
```

`points` are the points provided to compute the diagram. Each point (`site`) is associated with a `region`, a section of the 2D plane containing all points closer to the region's particular `site` than to any other.

`points`, like all coordinate data in this JSON, are indexed by unique UUID. This allows us to describe the region in terms of those UUIDs.

The primary use of that is with `vertices` - the vertices of the edges that bound the regions. Since any given Voronoi edge vertex is likely to be part of multiple edges, it looks better to describe that vertex by its associated UUID than to copy the same coordinate data multiple times.

`vertices` consist of vertices calculated when the diagram + vertices calculated when processing it. The latter case defines vertices that were found to fall outside the plane - x > 1 or < 0, y > 1 or < 0 - and consequently bounded within it.

### We keep the diagram within the plane by..

* Determining which of its four boundaries it would intersect with
* Figuring out where the boundary and the edge, two lines, would intersect
* Replacing the " outside the plane " vertice with that point of intersection

`regions` combines the above information:

* `siteId` indicates which `point` the region was computed with respect to
* `edges` is the edges bounding the region
    * Each `edge` indicates the two vertices composing it and, via `neighborSiteId`, the region immediately opposite to it

# How do we generate a diagram?

We first determine our list of points, taking (0, 0) as the top left corner of the plane:

```Python
basePoints = tuple((
    Point(.25, .25),
    Point(.40, .75),
    Point(.75, .25),
    Point(.60, .75),
    Point(.40, .40),
    Point(.30, .30),
    Point(.60, .30)
))
```

(The 0/1 bounding allows for intuitive specification of points. Instead of calculating the exact x and y coords in terms of the space width height you want, you can come up with points like (x = <25% of width>, y = <25% of width>) and scale the diagram data up appropriately after generating it.) 

We then generate the diagram.

```Python
from voronout.VoronoiDiagram import VoronoiDiagram
voronoiDiagram = VoronoiDiagram(basePoints = basePoints, planeWidth = <plane width>, planeHeight = <plane height>)
```

From there, we can either process the info ourselves..

```Python
for voronoiRegion in voronoiDiagram.voronoiRegions.values():
    for voronoiRegionEdge in voronoiRegion.edges:
        # Do whatever you want with the borders of the region..
```

.. or write it out as JSON for something else to process:

```Python
from voronout.VoronoiDiagramToJSON import toJson
toJson(voronoiDiagram = voronoiDiagram, voronoiJsonPath = "voronoi.json")
```

# How can we process a diagram?

Many ways - to quickly illustrate Voronout here, we'll draw generated diagrams with [Matplotlib](https://matplotlib.org/stable/).

With code like..

```Python

planeWidth = 600
planeHeight = 600

basePoints = tuple((Point(x = random.random(), y = random.random()) for _ in range(<numBasePoints>)))
voronoiDiagram = VoronoiDiagram(basePoints = basePoints, planeWidth = 600, planeHeight = 600)

pyplot.ylim(bottom = planeHeight, top = 0)

for voronoiRegion in voronoiDiagram.voronoiRegions.values():
    for voronoiRegionEdge in voronoiRegion.edges:
        vertexIdentifier0 = voronoiRegionEdge.vertexIdentifier0
        vertexIdentifier1 = voronoiRegionEdge.vertexIdentifier1

        vertex0 = diagramVertices[vertexIdentifier0] if vertexIdentifier0 in diagramVertices else diagramVertices[vertexIdentifier0]
        vertex1 = diagramVertices[vertexIdentifier1] if vertexIdentifier1 in diagramVertices else boundaryVertices[vertexIdentifier1]

        pyplot.plot([vertex0.x, vertex1.x], [vertex0.y, vertex1.y])
```

.. we can create diagrams like this (`numBasePoints = 5`)..

<img width="640" height="480" alt="voronout_5_points" src="https://github.com/user-attachments/assets/24373071-2b86-4972-a796-59d3c87b0752" />

.. or this (`numBasePoints = 20`)..

<img width="640" height="480" alt="voronout_20_points" src="https://github.com/user-attachments/assets/7c8f6b6b-1c33-4287-82db-6ed22fabe225" />

.. or this (`numBasePoints = 100`):

<img width="640" height="480" alt="voronout_100_points" src="https://github.com/user-attachments/assets/f47873c6-3dd4-43db-a0c2-0b0442813888" />
