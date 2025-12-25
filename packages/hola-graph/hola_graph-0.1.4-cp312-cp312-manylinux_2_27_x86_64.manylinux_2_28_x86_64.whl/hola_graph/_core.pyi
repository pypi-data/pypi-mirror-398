"""Type stubs for hola_graph - Python bindings for HOLA layout algorithm."""

from __future__ import annotations

from collections.abc import Iterator
from typing import overload

__version__: str

# Main layout function
def graph_from_tglf_file(path: str) -> Graph:
    """Build graph from .tglf file."""
    ...

def do_hola(graph: Graph, opts: HolaOpts | None = None) -> None:
    """Execute HOLA layout algorithm on a graph."""
    ...

version_info: tuple[int, int, int]

class Graph:
    """The Graph class represents graphs consisting of nodes and edges."""

    debug_output_path: str
    projection_debug_level: int

    def __init__(self) -> None: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[Node]: ...
    def __contains__(self, node_id: int) -> bool: ...
    def get_nodes(self) -> list[Node]: ...
    def add_nodes(self, nodes: list[Node]) -> None: ...
    def clear(self) -> None: ...

    # Node operations
    @overload
    def add_node(self, node: Node, take_ownership: bool = True) -> Node: ...
    @overload
    def add_node(self, w: float, h: float) -> Node: ...
    @overload
    def add_node(self, x: float, y: float, w: float, h: float) -> Node: ...
    def get_node(self, id: int) -> Node: ...
    def get_nodemap(self) -> dict[int, Node]: ...
    def has_node(self, id: int) -> bool: ...
    def remove_node(self, node: Node) -> None: ...
    def sever_node(self, node: Node) -> None: ...
    @overload
    def sever_remove_node(self, node: Node) -> None: ...
    @overload
    def sever_remove_node(self, nodeID: int) -> None: ...
    def get_num_nodes(self) -> int: ...

    # Edge operations
    @overload
    def add_edge(self, edge: Edge, take_ownership: bool = True) -> Edge: ...
    @overload
    def add_edge(self, src: Node, dst: Node) -> Edge: ...
    def has_edge(self, id: int) -> bool: ...
    def sever_edge(self, edge: Edge) -> None: ...
    def get_num_edges(self) -> int: ...

    # Serialization
    def to_tglf(self, use_external_ids: bool = False) -> str: ...
    def to_svg(self, use_external_ids: bool = False) -> str: ...

    # Graph properties
    def get_max_degree(self) -> int: ...
    def is_empty(self) -> bool: ...
    def is_tree(self) -> bool: ...
    def compute_avg_node_dim(self) -> float: ...
    def get_iel(self) -> float: ...
    def recompute_iel(self) -> float: ...

    # Layout transformations
    def rotate_90cw(self, opts: ColaOptions | None = None) -> None: ...
    def rotate_90acw(self, opts: ColaOptions | None = None) -> None: ...
    def rotate_180(self) -> None: ...
    def translate(self, dx: float, dy: float) -> None: ...
    def put_in_base_position(self) -> None: ...

    # Layout operations
    def destress(self, opts: ColaOptions | None = None) -> None: ...
    def solidify_aligned_edges(self, dim: int, opts: ColaOptions) -> None: ...
    def make_feasible(self, opts: ColaOptions) -> None: ...
    def project(self, opts: ColaOptions, dim: int, accept: int = ...) -> int: ...

    # Node position management
    def update_nodes_from_rects(
        self, xAxis: bool = True, yAxis: bool = True
    ) -> None: ...
    def push_node_positions(self) -> None: ...
    def pop_node_positions(self) -> None: ...

    # Edge properties
    def set_edge_thickness(self, t: float) -> None: ...
    def get_edge_thickness(self) -> float: ...
    def pad_all_nodes(self, dw: float, dh: float) -> None: ...

    # Routing
    def route(self, routingType: int) -> None: ...
    def clear_all_routes(self) -> None: ...
    def build_routes(self) -> None: ...

    # Constraints
    def clear_all_constraints(self) -> None: ...
    def set_corresponding_constraints(self, H: Graph) -> None: ...
    def get_sep_matrix(self) -> SepMatrix: ...

class Node:
    """A node (vertex) in the graph."""

    @property
    def id(self) -> int:
        """Access the unique ID of this instance."""
        ...

    @overload
    @staticmethod
    def allocate(w: float, h: float) -> Node:
        """Allocate a new Node with given width and height."""
        ...

    @overload
    @staticmethod
    def allocate(x: float, y: float, w: float, h: float) -> Node:
        """Allocate a new Node with given position and dimensions."""
        ...

    def __repr__(self) -> str: ...
    def get_dimensions(self) -> tuple[float, float]:
        """Return width and height as a tuple."""
        ...

    def get_degree(self) -> int:
        """Check the degree (number of incident Edges) of the Node."""
        ...

    def set_centre(self, cx: float, cy: float) -> None:
        """Set the position of the node by setting its centre coordinates."""
        ...

    def get_centre(self) -> avoid.Point:
        """Get the centre coordinates of the node."""
        ...

    def translate(self, dx: float, dy: float) -> None:
        """Update the position of the node by adding to its centre coordinates."""
        ...

    def set_dims(self, w: float, h: float) -> None:
        """Set the dimensions of the node."""
        ...

    def set_bounding_box(self, x: float, X: float, y: float, Y: float) -> None:
        """Set the bounding box which sets both dimensions and centre point."""
        ...

    def add_padding(self, dw: float, dh: float) -> None:
        """Add padding to the node's dimensions."""
        ...

    def get_bounding_box(self) -> BoundingBox:
        """Get the bounding box for this Node."""
        ...

    def set_external_id(self, id: int) -> None:
        """Set an externally-determined ID."""
        ...

    def get_external_id(self) -> int:
        """Get the external ID."""
        ...

    def is_root(self) -> bool:
        """Check whether this Node has been marked as being a root."""
        ...

    def set_is_root(self, isRoot: bool) -> None:
        """Say whether this Node is a root."""
        ...

    def set_graph(self, graph: Graph) -> None:
        """Tell the Node which Graph it belongs to."""
        ...

    def get_graph(self) -> Graph:
        """Access the Graph to which the Node belongs."""
        ...

    def remove_edge(self, edge: Edge) -> None:
        """Remove an incident Edge."""
        ...

    def copy_geometry(self, other: Node) -> None:
        """Give this Node the same coordinates and dimensions as another."""
        ...

class Edge:
    """An edge connecting two nodes in the graph."""

    def __repr__(self) -> str: ...
    @staticmethod
    def allocate(src: Node, dst: Node) -> Edge:
        """Allocate edge from source node to destination node."""
        ...

    def id(self) -> int:
        """Access the unique ID of this instance."""
        ...

    def set_graph(self, graph: Graph) -> None:
        """Tell the Edge which Graph it belongs to."""
        ...

    def sever(self) -> None:
        """Sever this Edge, removing it from the Nodes to which it is attached."""
        ...

    def get_bounding_box(self) -> BoundingBox:
        """Get the bounding box for the edge."""
        ...

    def add_route_point(self, x: float, y: float) -> None:
        """Add a point to the route."""
        ...

    def has_bend_nodes(self) -> bool:
        """Check whether this Edge has any bend nodes."""
        ...

    def rotate_90cw(self) -> None:
        """Rotate the connector route 90 degrees clockwise."""
        ...

    def rotate_90acw(self) -> None:
        """Rotate the connector route 90 degrees anticlockwise."""
        ...

    def rotate_180(self) -> None:
        """Rotate the connector route 180 degrees."""
        ...

    def translate(self, dx: float, dy: float) -> None:
        """Translate the connector route by a given amount in each dimension."""
        ...

    def clear_route_and_bends(self) -> None:
        """Clear the connector route and drop all bend nodes."""
        ...

    def build_route_from_bends(self) -> None:
        """Build a connector route based on the bend nodes."""
        ...

class BoundingBox:
    """A bounding box, given by the extreme coordinates."""

    x: float
    X: float
    y: float
    Y: float

    def __init__(
        self, x: float = 0, X: float = 0, y: float = 0, Y: float = 0
    ) -> None: ...
    def w(self) -> float:
        """Get the width of the box."""
        ...

    def h(self) -> float:
        """Get the height of the box."""
        ...

    def centre(self) -> avoid.Point:
        """Get the centre of the box."""
        ...

    def perimeter(self) -> float:
        """Compute the perimeter of the box."""
        ...

    def repr(self) -> str:
        """Write a simple representation of the bounding box."""
        ...

class HolaOpts:
    """Options for the HOLA layout algorithm."""

    defaultTreeGrowthDir: int
    treeLayoutScalar_nodeSep: float
    treeLayoutScalar_rankSep: float
    preferConvexTrees: bool
    peeledTreeRouting: int
    wholeTreeRouting: int
    orthoHubAvoidFlatTriangles: bool
    useACAforLinks: bool
    routingScalar_crossingPenalty: float
    routingScalar_segmentPenalty: float
    treePlacement_favourCardinal: float
    treePlacement_favourExternal: float
    treePlacement_favourIsolation: float
    expansion_doCostlierDimensionFirst: bool
    expansion_estimateMethod: int
    do_near_align: bool
    align_reps: int
    nearAlignScalar_kinkWidth: float
    nearAlignScalar_scope: float
    nodePaddingScalar: float
    preferredAspectRatio: float
    preferredTreeGrowthDir: int
    putUlcAtOrigin: bool

    def __init__(self) -> None: ...

class ColaOptions:
    """Options for libcola layout methods."""

    idealEdgeLength: float
    preventOverlaps: bool
    solidifyAlignedEdges: bool
    xAxis: bool
    yAxis: bool
    makeFeasible: bool
    makeFeasible_xBorder: float
    makeFeasible_yBorder: float
    useNeighbourStress: bool
    nbrStressIELScalar: float
    useMajorization: bool
    useScaling: bool

    def __init__(self) -> None: ...

class Tree:
    """A tree structure for hierarchical layout."""

    def __init__(self, G: Graph, root: Node) -> None: ...
    def symmetricLayout(
        self,
        growthDir: int,
        nodeSep: float,
        rankSep: float,
        convexOrdering: bool = False,
    ) -> None:
        """Apply the Symmetric Layout algorithm."""
        ...

    def flip(self) -> None:
        """Flip the tree's layout over the axis running through the root node."""
        ...

    def translate(self, vect: avoid.Point) -> None:
        """Translate the tree's layout by a given vector."""
        ...

    def rotate(self, dg: int) -> None:
        """Rotate the tree's layout to attain a desired growth direction."""
        ...

    def underlyingGraph(self) -> Graph:
        """Access the Tree's underlying Graph."""
        ...

    def getRootNode(self) -> Node:
        """Access the Tree's root Node."""
        ...

    def getRootNodeID(self) -> int:
        """Check the ID of the root node."""
        ...

    def isSymmetrical(self) -> bool:
        """Check whether the layout is symmetrical."""
        ...

    def size(self) -> int:
        """Check how many nodes are in the tree."""
        ...

    def repr(self) -> str:
        """Write a string representation of this Tree."""
        ...

class ACALayout:
    """Implements the Adaptive Constrained Alignment (ACA) algorithm."""

    def __init__(self, G: Graph) -> None: ...
    def createAlignments(self) -> None:
        """Creates alignments greedily until any further would create edge overlaps."""
        ...

    def createOneAlignment(self) -> bool:
        """Creates one alignment and returns True if a new alignment was created."""
        ...

    def layout(self) -> None:
        """Do an initial stress-minimising layout, then create alignments."""
        ...

    def removeOverlaps(self) -> None:
        """Do an FD layout with overlap prevention, then stop."""
        ...

    def layoutWithCurrentConstraints(self) -> None:
        """Run layout with current constraints."""
        ...

    def updateGraph(self) -> None:
        """Update the Graph with positions and constraints."""
        ...

    def addBendPointPenalty(self, b: bool) -> None:
        """Control whether we avoid making bend points."""
        ...

    def favourLongEdges(self, b: bool) -> None:
        """Prefer long edges instead of ones that are close to aligned."""
        ...

    def postponeLeaves(self, b: bool) -> None:
        """Say whether alignment of leaf edges should be saved for last."""
        ...

    def allAtOnce(self, b: bool) -> None:
        """Say whether alignment choices should alternate with stress minimisation."""
        ...

    def aggressiveOrdering(self, b: bool) -> None:
        """Say whether to consider changing orthogonal ordering of nodes."""
        ...

    def setAvoidNodeOverlaps(self, avoidOverlaps: bool) -> None:
        """Specifies whether non-overlap constraints should be generated."""
        ...

class SepMatrix:
    """Separation matrix for constraint management."""

    def addSep(self, id1: int, id2: int, gt: int, sd: int, st: int, gap: float) -> None:
        """Add a constraint."""
        ...

    def hAlign(self, id1: int, id2: int) -> None:
        """Align a pair of nodes horizontally."""
        ...

    def vAlign(self, id1: int, id2: int) -> None:
        """Align a pair of nodes vertically."""
        ...

    def free(self, id1: int, id2: int) -> None:
        """Free a pair of Nodes; remove the SepPair completely."""
        ...

    def clear(self) -> None:
        """Clear all constraints."""
        ...

    def removeNode(self, id: int) -> None:
        """Remove all records for the Node of given ID."""
        ...

    def areHAligned(self, id1: int, id2: int) -> bool:
        """Check whether two nodes are horizontally aligned."""
        ...

    def areVAligned(self, id1: int, id2: int) -> bool:
        """Check whether two nodes are vertically aligned."""
        ...

    def toString(self) -> str:
        """Returns a textual description."""
        ...

# Submodule for libavoid geometric types
class avoid:
    """libavoid geometric types for obstacle avoidance routing."""

    class Point:
        """The Point class defines a point in the plane."""

        x: float
        y: float
        id: int
        vn: int

        def __init__(self, x: float = 0, y: float = 0) -> None: ...
        def __eq__(self, rhs: object) -> bool: ...
        def __ne__(self, rhs: object) -> bool: ...
        def __add__(self, rhs: avoid.Point) -> avoid.Point: ...
        def __sub__(self, rhs: avoid.Point) -> avoid.Point: ...
        def __getitem__(self, dimension: int) -> float: ...
        def equals(self, rhs: avoid.Point, epsilon: float = ...) -> bool: ...

    class Box:
        """A bounding box represented by top-left and bottom-right corners."""

        min: avoid.Point
        max: avoid.Point

        def __init__(self) -> None: ...
        def length(self, dimension: int) -> float: ...
        def width(self) -> float: ...
        def height(self) -> float: ...

    class Polygon:
        """A dynamic Polygon to which points can be added and removed."""

        _id: int

        def __init__(self, n: int = 0) -> None: ...
        def clear(self) -> None: ...
        def empty(self) -> bool: ...
        def size(self) -> int: ...
        def id(self) -> int: ...
        def at(self, index: int) -> avoid.Point: ...
        def setPoint(self, index: int, point: avoid.Point) -> None: ...
        def simplify(self) -> avoid.Polygon: ...
        def translate(self, xDist: float, yDist: float) -> None: ...

    class Rectangle(Polygon):
        """A Rectangle, a simpler way to define square or rectangular shapes."""

        @overload
        def __init__(self, topLeft: avoid.Point, bottomRight: avoid.Point) -> None: ...
        @overload
        def __init__(
            self, centre: avoid.Point, width: float, height: float
        ) -> None: ...
