from .Boundary import Boundary
from .Point import Point

from .edges.VoronoiEdge import VoronoiEdge

from .edges.VoronoiEdgeData import VoronoiEdgeData

from .regions.VoronoiRegion import VoronoiRegion
from .regions.VoronoiRegionData import VoronoiRegionData

from enum import Enum

from itertools import repeat

from scipy.spatial import Voronoi
from uuid import uuid4

import numpy as np

class _BoundingNeeded(Enum):
    X_AND_Y = 1
    X = 2
    Y = 3

# Minimum basePoints that the underlying qHull requires.
minBasePoints = 3

class VoronoiDiagram:
    def __init__(self, basePoints: tuple[Point], planeWidth: float, planeHeight: float):
        # Make sure basePoints fits the minBasePoints/within (0, 0) -> (1, 1) constraints.
        self._validateBasePoints(basePoints = basePoints)

        # We expect basePoints to have 0, 0 (top-left), but scipy.spatial does 0, 0 (bottom-left) - so convert.
        sciPySpatialPoints = np.array(tuple(basePoint.convertPointBase() for basePoint in basePoints))        
        self._voronoiDiagram = Voronoi(sciPySpatialPoints)

        # _spatial.. values are with respect to the diagram. 
        self._spatialSites = { uuid4(): Point(x = spatialPoint[0], y = spatialPoint[1]) for spatialPoint in self._voronoiDiagram.points }
        self._spatialSiteKeys = tuple(self._spatialSites.keys())

        self._spatialDiagramVertices = { uuid4(): Point(x = spatialDiagramVertex[0], y = spatialDiagramVertex[1]) for spatialDiagramVertex in self._voronoiDiagram.vertices}
        spatialDiagramVerticesKeys = list(self._spatialDiagramVertices.keys())

        # { regionId: <list of VoronoiEdgeIdData describing the edges that bound the region> }
        self._spatialSiteRegionBoundaries: dict[uuid4, list[VoronoiEdge]] = { siteKey: [] for siteKey in self._spatialSiteKeys }

        # Stores vertices determined as a result of " bounding " calculations.
        self._spatialBoundingVertices: dict[uuid4, Point] = {}

        # Store vertices that get bounded for later deletion.
        boundedDiagramVertices = []

        # voronoiRegionsInfo[pointIndex] describes the region identified by self._spatialSitesKeys[pointIndex].
        voronoiRegionsInfo = tuple((self._makeVoronoiRegionData(regionSiteIdIndex = pointIndex) for pointIndex in range(len(self._voronoiDiagram.points))))
        
        # Handling len(basePoints) = 3 case where Voronoi diagram is created with only one vertex.
        numBasePoints = len(basePoints)
        vertices = self._voronoiDiagram.ridge_vertices
        verticesToZip = vertices if numBasePoints > minBasePoints else tuple(repeat(vertices[0], numBasePoints))
        
        # Each ([vertex0, vertex1], [site0, site1]) should concern the same edge.
        edgeVerticesAndSites = () if False else zip(verticesToZip, self._voronoiDiagram.ridge_points)

        for ([edgeVertex0Index, edgeVertex1Index], [edgeSite0Index, edgeSite1Index]) in edgeVerticesAndSites:
            vertex0OutOfDiagram = edgeVertex0Index == -1
            vertex1OutOfDiagram = edgeVertex1Index == -1

            # None indicates that the relevant vertex is outside the diagram's bounds and must be calculated.
            edgeVertex0Id = None if vertex0OutOfDiagram else spatialDiagramVerticesKeys[edgeVertex0Index]
            edgeVertex1Id = None if vertex1OutOfDiagram else spatialDiagramVerticesKeys[edgeVertex1Index]

            edgeVertex0 = None if vertex0OutOfDiagram else self._spatialDiagramVertices[edgeVertex0Id]
            edgeVertex1 = None if vertex1OutOfDiagram else self._spatialDiagramVertices[edgeVertex1Id]

            edgeSite0Id = self._spatialSiteKeys[edgeSite0Index]
            edgeSite1Id = self._spatialSiteKeys[edgeSite1Index]

            # Add edge info to both regions containing the edge.
            site0Edge = VoronoiEdge(vertex0Id = edgeVertex0Id, vertex1Id = edgeVertex1Id, neighborSiteId = edgeSite1Id)
            site0EdgeData = VoronoiEdgeData(vertex0 = edgeVertex0, vertex1 = edgeVertex1, edgeInIds = site0Edge)
            voronoiRegionsInfo[edgeSite0Index].addEdgesData(edgeVertex0Index = edgeVertex0Index, edgeVertex1Index = edgeVertex1Index, neighborSiteIndex = edgeSite1Index, edgeData = site0EdgeData)
            
            site1Edge = VoronoiEdge(vertex0Id = edgeVertex0Id, vertex1Id = edgeVertex1Id, neighborSiteId = edgeSite0Id)
            site1EdgeData = VoronoiEdgeData(vertex0 = edgeVertex0, vertex1 = edgeVertex1, edgeInIds = site1Edge)
            voronoiRegionsInfo[edgeSite1Index].addEdgesData(edgeVertex0Index = edgeVertex1Index, edgeVertex1Index = edgeVertex0Index, neighborSiteIndex = edgeSite0Index, edgeData = site1EdgeData)

        for voronoiRegionInfo in voronoiRegionsInfo:
            regionId = voronoiRegionInfo.siteId
            for voronoiRegionEdge in voronoiRegionInfo.edges():
                edgeVertex0 = voronoiRegionEdge.vertex0
                edgeVertex1 = voronoiRegionEdge.vertex1

                edgeVertex0Id = voronoiRegionEdge.vertex0Id()
                edgeVertex1Id = voronoiRegionEdge.vertex1Id()

                vertex0OutsideDiagram = not voronoiRegionEdge.vertex0 and not voronoiRegionEdge.vertex0Id()
                vertex1OutsideDiagram = not voronoiRegionEdge.vertex1 and not voronoiRegionEdge.vertex1Id()

                neighborSiteId = voronoiRegionEdge.neighborSiteId()

                if not (vertex0OutsideDiagram or vertex1OutsideDiagram):
                    vertex0NeedsBounding = self._vertexNeedsBounding(vertex = edgeVertex0)
                    vertex1NeedsBounding = self._vertexNeedsBounding(vertex = edgeVertex1)

                    maybeBoundedEdgeVertex0 = self._boundVertex(vertex = edgeVertex0, otherVertex = edgeVertex1, boundingNeeded = vertex0NeedsBounding) if vertex0NeedsBounding else None
                    latestEdgeVertex0 = maybeBoundedEdgeVertex0 or edgeVertex0

                    edgeVertex0Id = voronoiRegionEdge.vertex0Id()
                    if maybeBoundedEdgeVertex0 and edgeVertex0Id not in boundedDiagramVertices:
                        boundedDiagramVertices.append(edgeVertex0Id)

                    edgeVertex1Id = voronoiRegionEdge.vertex1Id()
                    maybeBoundedEdgeVertex1 = self._boundVertex(vertex = edgeVertex1, otherVertex = latestEdgeVertex0, boundingNeeded = vertex1NeedsBounding) if vertex1NeedsBounding else None
                    latestEdgeVertex1 = maybeBoundedEdgeVertex1 or edgeVertex1

                    if maybeBoundedEdgeVertex1 and edgeVertex1Id not in boundedDiagramVertices:
                        boundedDiagramVertices.append(edgeVertex1Id)

                    latestEdgeVertex0Id = self._getBoundingVertexId(boundingVertex = maybeBoundedEdgeVertex0) if maybeBoundedEdgeVertex0 else edgeVertex0Id

                    if maybeBoundedEdgeVertex0:
                        self._spatialBoundingVertices[latestEdgeVertex0Id] = latestEdgeVertex0
                    
                    latestEdgeVertex1Id = self._getBoundingVertexId(boundingVertex = maybeBoundedEdgeVertex1) if maybeBoundedEdgeVertex1 else edgeVertex1Id

                    if maybeBoundedEdgeVertex1:
                        self._spatialBoundingVertices[latestEdgeVertex1Id] = latestEdgeVertex1

                    latestEdge = VoronoiEdge(vertex0Id = latestEdgeVertex0Id, vertex1Id = latestEdgeVertex1Id, neighborSiteId = neighborSiteId)
                    self._spatialSiteRegionBoundaries[regionId].append(latestEdge)
                elif vertex0OutsideDiagram or vertex1OutsideDiagram:
                    pointInsideDiagramId = edgeVertex0Id if vertex1OutsideDiagram else edgeVertex1Id
                    
                    pointInsideDiagram = self._spatialDiagramVertices[pointInsideDiagramId]
                    pointInsideDiagramNeedsBounding = self._vertexNeedsBounding(vertex = pointInsideDiagram)

                    regionSite = self._spatialSites[regionId]
                    neighborSite = self._spatialSites[neighborSiteId]

                    betweenRegionsMidpoint = Point.midpoint(p1 = regionSite, p2 = neighborSite)
                    maybeRegionContainingCalculatedMidpoint = self._maybeReturnSiteOfRegionContainingMidpoint(calculatedMidpoint = betweenRegionsMidpoint, calculationPoint1 = regionSite, calculationPoint2 = neighborSite)
                    # Sometimes, the calculated midpoint is within a region. We try to avoid this by reflecting it over the closest vertex.
                    reflectedSitesMidpoint = None if not maybeRegionContainingCalculatedMidpoint else self._reflectPointAroundVertex(point = betweenRegionsMidpoint, vertex = pointInsideDiagram)

                    latestMidpoint = reflectedSitesMidpoint or betweenRegionsMidpoint

                    maybeBoundedPointInsideDiagram = self._boundVertex(vertex = pointInsideDiagram, otherVertex = latestMidpoint, boundingNeeded = pointInsideDiagramNeedsBounding) if pointInsideDiagramNeedsBounding else None
                    latestPointInsideDiagram = maybeBoundedPointInsideDiagram or pointInsideDiagram

                    if maybeBoundedPointInsideDiagram and pointInsideDiagramId not in boundedDiagramVertices:
                        boundedDiagramVertices.append(pointInsideDiagramId)

                    closestBoundary = Boundary.findBoundaryInLineDirection(linePoint1 = latestPointInsideDiagram, linePoint2 = latestMidpoint)
                    boundaryIntersectionPoint = Boundary.boundaryLineIntersectionPoint(lineFirstPoint = latestPointInsideDiagram, lineSecondPoint = latestMidpoint, boundary = closestBoundary)

                    boundaryIntersectionNeedsBounding = self._vertexNeedsBounding(vertex = boundaryIntersectionPoint)
                    maybeBoundedIntersection = self._boundVertex(vertex = boundaryIntersectionPoint, otherVertex = latestPointInsideDiagram, boundingNeeded = boundaryIntersectionNeedsBounding) if boundaryIntersectionNeedsBounding else None

                    latestPointInsideDiagramId = self._getBoundingVertexId(boundingVertex = maybeBoundedPointInsideDiagram) if maybeBoundedPointInsideDiagram else pointInsideDiagramId

                    if maybeBoundedPointInsideDiagram:
                        self._spatialBoundingVertices[latestPointInsideDiagramId] = latestPointInsideDiagram

                    latestBoundaryIntersection = maybeBoundedIntersection or boundaryIntersectionPoint        
                    boundaryIntersectionPointId = self._getBoundingVertexId(boundingVertex = latestBoundaryIntersection)
                    self._spatialBoundingVertices[boundaryIntersectionPointId] = latestBoundaryIntersection

                    latestEdge = VoronoiEdge(vertex0Id = boundaryIntersectionPointId, vertex1Id = latestPointInsideDiagramId, neighborSiteId = neighborSiteId) if vertex0OutsideDiagram else VoronoiEdge(edgeVertex0Id = latestPointInsideDiagramId, edgeVertex1Id = boundaryIntersectionPointId, neighborSiteId = neighborSiteId)
                    self._spatialSiteRegionBoundaries[regionId].append(latestEdge)
                else:
                    # Should only be needed for assumedly impossible cases like bertex0/1 both being outside the diagram.
                    raise ValueError(f"Could not handle unexpected vertex0/1OutsideDiagram ({vertex0OutsideDiagram}, {vertex1OutsideDiagram})")

        for boundedDiagramVertex in boundedDiagramVertices:
            del self._spatialDiagramVertices[boundedDiagramVertex]

        self.voronoiRegions = { spatialSiteKey: self._makeVoronoiRegion(regionSiteIdentifier = spatialSiteKey) for spatialSiteKey in self._spatialSiteKeys }

        # Public-facing values are 0, 0 (top-left).
        self.points = {pointId: point.convertPointBase().scale(widthScalar = planeWidth, heightScalar = planeHeight) for (pointId, point) in self._spatialSites.items()}
        
        convertedDiagramVertices = {diagramVertexId: diagramVertex.convertPointBase().scale(widthScalar = planeWidth, heightScalar = planeHeight) for (diagramVertexId, diagramVertex) in self._spatialDiagramVertices.items()}
        convertedBoundingVertices = {boundingVertexId: boundingVertex.convertPointBase().scale(widthScalar = planeWidth, heightScalar = planeHeight) for (boundingVertexId, boundingVertex) in self._spatialBoundingVertices.items()}

        self.vertices = convertedDiagramVertices | convertedBoundingVertices
        
    def _validateBasePoints(self, basePoints: tuple[Point]) -> None:
        if len(basePoints) < minBasePoints:
            raise ValueError(f"Too few points specified, {basePoints} - need minimum {minBasePoints}")
        
        allWithinBounds = all((0 <= basePoint.x <= 1 and 0 <= basePoint.y <= 1 for basePoint in basePoints))
        if not allWithinBounds:
            raise ValueError(f"{basePoints} violate the x/y must be >= 0, <= 1 constraint")

    def _makeVoronoiRegionData(self, regionSiteIdIndex: int) -> VoronoiRegionData:
        regionSiteId = self._spatialSiteKeys[regionSiteIdIndex]
        return VoronoiRegionData(siteId = regionSiteId)

    def _getBoundingVertexId(self, boundingVertex: Point) -> uuid4:
        extantIdSearchResult = tuple((vertexId for (vertexId, vertex) in self._spatialBoundingVertices.items() if vertex == boundingVertex))
        if extantIdSearchResult:
            # Return the first (and only) result.
            return extantIdSearchResult[0]
        else:
            # Return a new ID that will be stored.
            return uuid4()

    def _pointXWithinBounds(self, point: Point) -> bool:
        return 0 <= point.x <= 1
    
    def _pointYWithinBounds(self, point: Point) -> bool:
        return 0 <= point.y <= 1
    
    def _vertexNeedsBounding(self, vertex: Point) -> _BoundingNeeded | None:
        vertexXUnbounded = not self._pointXWithinBounds(point = vertex)
        vertexYUnbounded = not self._pointYWithinBounds(point = vertex)

        if vertexXUnbounded and vertexYUnbounded:
            return _BoundingNeeded.X_AND_Y
        elif vertexXUnbounded and not vertexYUnbounded:
            return _BoundingNeeded.X
        elif not vertexXUnbounded and vertexYUnbounded:
            return _BoundingNeeded.Y
        else:
            return None
        
    def _boundVertex(self, vertex: Point, otherVertex: Point, boundingNeeded: _BoundingNeeded) -> Point:
        match boundingNeeded:
            case _BoundingNeeded.X_AND_Y:
                vertexBoundedOnX = Boundary.boundVertexOnX(vertex = vertex, otherVertex = otherVertex)
                
                shouldBoundOnY = 0 <= vertexBoundedOnX.x <= 1 and not (0 <= vertexBoundedOnX.y <= 1)
                vertexBoundedOnY = Boundary.boundVertexOnY(vertex = vertexBoundedOnX, otherVertex = otherVertex) if shouldBoundOnY else None
                
                return vertexBoundedOnY or vertexBoundedOnX
            case _BoundingNeeded.X:
                return Boundary.boundVertexOnX(vertex = vertex, otherVertex = otherVertex)
            case _BoundingNeeded.Y:
                return Boundary.boundVertexOnY(vertex = vertex, otherVertex = otherVertex)
            
    def _maybeReturnSiteOfRegionContainingMidpoint(self, calculatedMidpoint: Point, calculationPoint1: Point, calculationPoint2: Point) -> Point:
        otherSites = tuple((otherSite for otherSite in self._spatialSites.values() if otherSite != calculationPoint1 and otherSite != calculationPoint2))

        calculationPoint1Dist = Point.distance(p1 = calculatedMidpoint, p2 = calculationPoint1)
        calculationPoint2Dist = Point.distance(p1 = calculatedMidpoint, p2 = calculationPoint2)

        otherSiteDistances = { otherSite: Point.distance(p1 = calculatedMidpoint, p2 = otherSite) for otherSite in otherSites }
        # Filter otherSiteDistances down to any closer to otherSite than calculationPoint1 and calculationPoint2.
        otherSiteDistancesFiltered = tuple((otherSite for (otherSite, otherSiteDistance) in otherSiteDistances.items() if otherSiteDistance < calculationPoint1Dist and otherSiteDistance < calculationPoint2Dist))
        
        if otherSiteDistancesFiltered:
            # .. return the first, very likely only, result.
            return otherSiteDistancesFiltered[0]
        else:
            # .. return None, because the midpoint is on a line.
            return None
        
    def _regionContainsMidpoint(self, midpoint: Point, regionSite: Point) -> bool:
        regionMidpointDistance = Point.distance(p1 = midpoint, p2 = regionSite)
        otherSiteDistances = tuple((Point.distance(p1 = midpoint, p2 = otherSite) for otherSite in self._spatialSites.values() if otherSite != regionSite))
        return all((regionMidpointDistance < otherSiteDistance for otherSiteDistance in otherSiteDistances))
            
    def _reflectPointAroundVertex(self, point: Point, vertex: Point) -> Point:
        pointDy = vertex.y - point.y
        pointDx = vertex.x - point.x

        reflectionY = vertex.y + pointDy
        reflectionX = vertex.x + pointDx
        
        reflection = Point(x = reflectionX, y = reflectionY)
        return reflection
    
    def _reflectSitesAndCalculateMidpoint(self, site1: Point, site2: Point, vertex: Point) -> Point:
        reflectedSite1 = self._reflectPointAroundVertex(point = site1, vertex = vertex)
        reflectedSite2 = self._reflectPointAroundVertex(point = site2, vertex = vertex)

        return Point.midpoint(p1 = reflectedSite1, p2 = reflectedSite2)
    
    def _makeVoronoiRegion(self, regionSiteIdentifier: uuid4) -> VoronoiRegion:
        regionEdges = self._spatialSiteRegionBoundaries[regionSiteIdentifier]
        return VoronoiRegion(siteId = regionSiteIdentifier, edges = regionEdges)