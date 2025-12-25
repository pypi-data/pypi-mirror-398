"""Enhanced Python utilities for hola_graph.

This module provides Pythonic convenience functions and classes
that wrap the core hola_graph C++ bindings with additional functionality.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from hola_graph import _core
from hola_graph._core import Edge, Graph, Node, do_hola, graph_from_tglf_file

# =============================================================================
# Input Validation
# =============================================================================


def validate_dimensions(width: float, height: float, context: str = "") -> None:
    """Validate that node dimensions are positive.

    Args:
        width: Node width to validate.
        height: Node height to validate.
        context: Optional context string for error messages.

    Raises:
        ValueError: If width or height is not positive.
    """
    prefix = f"{context}: " if context else ""
    if width <= 0:
        raise ValueError(f"{prefix}width must be positive, got {width}")
    if height <= 0:
        raise ValueError(f"{prefix}height must be positive, got {height}")


def validate_path(
    path: str | Path, must_exist: bool = True, expected_suffix: str | None = None
) -> Path:
    """Validate a file path.

    Args:
        path: Path to validate.
        must_exist: If True, raise error if file doesn't exist.
        expected_suffix: Expected file extension (e.g., ".tglf").

    Returns:
        Validated Path object.

    Raises:
        FileNotFoundError: If must_exist is True and file doesn't exist.
        ValueError: If expected_suffix is set and doesn't match.
    """
    path = Path(path)
    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if expected_suffix and path.suffix.lower() != expected_suffix.lower():
        raise ValueError(f"Expected {expected_suffix} file, got: {path.suffix}")
    return path


def create_node(
    width: float,
    height: float,
    x: float | None = None,
    y: float | None = None,
) -> Node:
    """Create a new Node with validation.

    This is a validated wrapper around Node.allocate().

    Args:
        width: Node width (must be positive).
        height: Node height (must be positive).
        x: Optional x position.
        y: Optional y position.

    Returns:
        A new Node instance.

    Raises:
        ValueError: If dimensions are not positive.

    Example:
        >>> node = create_node(10, 20)  # Creates node with w=10, h=20
        >>> node = create_node(10, 20, x=50, y=100)  # With position
    """
    validate_dimensions(width, height, context="create_node")
    if x is not None and y is not None:
        return Node.allocate(x, y, width, height)
    return Node.allocate(width, height)


def load_graph(path: str | Path) -> Graph:
    """Load a graph from a TGLF file with path validation.

    Args:
        path: Path to the TGLF file.

    Returns:
        The loaded Graph.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a .tglf file.
    """
    validated_path = validate_path(path, must_exist=True, expected_suffix=".tglf")
    return graph_from_tglf_file(str(validated_path))


def save_svg(graph: Graph, path: str | Path) -> None:
    """Save a graph to an SVG file.

    Args:
        graph: The graph to save.
        path: Output path for the SVG file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(graph.to_svg())


def save_tglf(graph: Graph, path: str | Path, use_external_ids: bool = False) -> None:
    """Save a graph to a TGLF file.

    Args:
        graph: The graph to save.
        path: Output path for the TGLF file.
        use_external_ids: Whether to use external IDs in the output.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(graph.to_tglf(use_external_ids))


@contextmanager
def layout_context(graph: Graph):
    """Context manager that saves and restores node positions.

    Useful for experimenting with layouts without losing the original positions.

    Example:
        >>> with layout_context(graph):
        ...     do_hola(graph)
        ...     # positions are restored after the context exits
    """
    graph.push_node_positions()
    try:
        yield graph
    finally:
        graph.pop_node_positions()


def apply_hola(graph: Graph, opts: _core.HolaOpts | None = None) -> Graph:
    """Apply HOLA layout and return the graph (for chaining).

    Args:
        graph: The graph to layout.
        opts: Optional HolaOpts configuration.

    Returns:
        The same graph (for method chaining).
    """
    if opts is not None:
        do_hola(graph, opts)
    else:
        do_hola(graph)
    return graph


def create_graph(*edges: tuple[tuple[float, float], tuple[float, float]]) -> Graph:
    """Create a graph from a list of edge specifications.

    Each edge is specified as ((w1, h1), (w2, h2)) where (w, h) are node dimensions.
    Nodes are created automatically and connected.

    Example:
        >>> g = create_graph(
        ...     ((10, 10), (20, 20)),  # edge from node1 to node2
        ...     ((20, 20), (15, 15)),  # edge from node2 to node3
        ... )

    Args:
        edges: Tuples of ((w1, h1), (w2, h2)) specifying edges.

    Returns:
        A new Graph with the specified structure.

    Raises:
        ValueError: If any node dimensions are not positive.
    """
    g = Graph()
    node_cache = {}

    for i, ((w1, h1), (w2, h2)) in enumerate(edges):
        validate_dimensions(w1, h1, context=f"edge {i} source node")
        validate_dimensions(w2, h2, context=f"edge {i} target node")

        key1 = (w1, h1)
        key2 = (w2, h2)

        if key1 not in node_cache:
            n1 = Node.allocate(w1, h1)
            g.add_node(n1)
            node_cache[key1] = n1
        else:
            n1 = node_cache[key1]

        if key2 not in node_cache:
            n2 = Node.allocate(w2, h2)
            g.add_node(n2)
            node_cache[key2] = n2
        else:
            n2 = node_cache[key2]

        g.add_edge(n1, n2)

    return g


def iter_edges(graph: Graph) -> Iterator[Edge]:
    """Iterate over all edges in the graph.

    Note: This requires accessing the internal edge lookup which may
    not be directly exposed. This is a convenience wrapper.

    Args:
        graph: The graph to iterate.

    Yields:
        Edge objects from the graph.
    """
    # Note: Edge iteration requires getEdgeLookup which may not be exposed
    # This is a placeholder that documents the intended API
    raise NotImplementedError(
        "Edge iteration requires C++ binding support for getEdgeLookup()"
    )


def graph_stats(graph: Graph) -> dict:
    """Get statistics about a graph.

    Args:
        graph: The graph to analyze.

    Returns:
        Dictionary with graph statistics.
    """
    stats = {
        "num_nodes": graph.get_num_nodes(),
        "num_edges": graph.get_num_edges(),
        "is_empty": graph.is_empty(),
        "is_tree": graph.is_tree(),
        "max_degree": graph.get_max_degree(),
        "avg_node_dim": graph.compute_avg_node_dim() if not graph.is_empty() else 0.0,
        "ideal_edge_length": graph.get_iel() if not graph.is_empty() else 0.0,
    }
    return stats


def print_graph_info(graph: Graph) -> None:
    """Print information about a graph.

    Args:
        graph: The graph to describe.
    """
    stats = graph_stats(graph)
    print("Graph Statistics:")
    print(f"  Nodes: {stats['num_nodes']}")
    print(f"  Edges: {stats['num_edges']}")
    print(f"  Is Tree: {stats['is_tree']}")
    print(f"  Max Degree: {stats['max_degree']}")
    print(f"  Avg Node Dimension: {stats['avg_node_dim']:.2f}")
    print(f"  Ideal Edge Length: {stats['ideal_edge_length']:.2f}")


class GraphBuilder:
    """Fluent builder for creating graphs.

    Example:
        >>> g = (GraphBuilder()
        ...     .add_node(10, 10, name='A')
        ...     .add_node(20, 20, name='B')
        ...     .add_edge('A', 'B')
        ...     .build())
    """

    def __init__(self) -> None:
        self._graph: Graph = Graph()
        self._nodes: dict[str | int, Node] = {}

    def add_node(
        self,
        width: float,
        height: float,
        x: float | None = None,
        y: float | None = None,
        name: str | None = None,
    ) -> GraphBuilder:
        """Add a node to the graph.

        Args:
            width: Node width (must be positive).
            height: Node height (must be positive).
            x: Optional x position.
            y: Optional y position.
            name: Optional name for referencing in add_edge.

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If dimensions are not positive.
        """
        validate_dimensions(width, height, context="GraphBuilder.add_node")
        if x is not None and y is not None:
            node = Node.allocate(x, y, width, height)
        else:
            node = Node.allocate(width, height)

        self._graph.add_node(node)

        if name is not None:
            self._nodes[name] = node
        else:
            self._nodes[node.id] = node

        return self

    def add_edge(self, src: str | int | Node, dst: str | int | Node) -> GraphBuilder:
        """Add an edge between two nodes.

        Args:
            src: Source node (by name, ID, or Node object).
            dst: Destination node (by name, ID, or Node object).

        Returns:
            Self for method chaining.

        Raises:
            KeyError: If node name/ID not found.
        """
        if isinstance(src, Node):
            src_node = src
        else:
            src_node = self._nodes[src]

        if isinstance(dst, Node):
            dst_node = dst
        else:
            dst_node = self._nodes[dst]

        self._graph.add_edge(src_node, dst_node)
        return self

    def build(self) -> Graph:
        """Build and return the graph.

        Returns:
            The constructed Graph.
        """
        return self._graph

    def layout(self, opts: _core.HolaOpts | None = None) -> GraphBuilder:
        """Apply HOLA layout to the graph.

        Args:
            opts: Optional layout options.

        Returns:
            Self for method chaining.
        """
        apply_hola(self._graph, opts)
        return self


# Convenience presets for HolaOpts
def compact_layout_opts() -> _core.HolaOpts:
    """Create HolaOpts preset for compact layouts.

    Returns:
        HolaOpts configured for dense, compact layouts.
    """
    opts = _core.HolaOpts()
    opts.nodePaddingScalar = 0.5
    return opts


def spacious_layout_opts() -> _core.HolaOpts:
    """Create HolaOpts preset for spacious, readable layouts.

    Returns:
        HolaOpts configured for well-spaced layouts.
    """
    opts = _core.HolaOpts()
    opts.nodePaddingScalar = 2.0
    return opts


# =============================================================================
# NetworkX Interoperability
# =============================================================================


def to_networkx(graph: Graph, include_positions: bool = True):
    """Convert a hola_graph Graph to a NetworkX graph.

    Requires networkx to be installed.

    Args:
        graph: The hola_graph Graph to convert.
        include_positions: If True, include node positions as 'pos' attribute.

    Returns:
        A networkx.Graph with nodes and edges from the hola_graph graph.

    Raises:
        ImportError: If networkx is not installed.

    Example:
        >>> import hola_graph_utils as pu
        >>> g = pu.load_graph("graph.tglf")
        >>> do_hola(g)
        >>> nx_graph = pu.to_networkx(g)
        >>> import matplotlib.pyplot as plt
        >>> import networkx as nx
        >>> nx.draw(nx_graph, pos=nx.get_node_attributes(nx_graph, 'pos'))
    """
    try:
        import networkx as nx
    except ImportError as err:
        raise ImportError(
            "NetworkX is required for this function. "
            "Install it with: pip install networkx"
        ) from err

    G = nx.Graph()

    # Add nodes with attributes
    for node in graph.get_nodes():
        node_id = node.id
        dims = node.get_dimensions()
        centre = node.get_centre()

        node_attrs: dict[str, Any] = {
            "width": dims[0],
            "height": dims[1],
        }

        if include_positions:
            node_attrs["pos"] = (centre.x, centre.y)

        G.add_node(node_id, **node_attrs)

    # Add edges - we need to infer edges from node connections
    # This requires iterating over nodes and their edges
    # Since Edge iteration isn't directly exposed, we use TGLF parsing
    tglf = graph.to_tglf()
    _parse_tglf_edges(G, tglf)

    return G


def _parse_tglf_edges(nx_graph, tglf_content: str) -> None:
    """Parse edges from TGLF content and add to NetworkX graph.

    TGLF format has nodes first, then edges after a '#' separator,
    or can have explicit EDGES section.

    Args:
        nx_graph: NetworkX graph to add edges to.
        tglf_content: TGLF file content as string.
    """
    in_edges_section = False
    for line in tglf_content.split("\n"):
        line = line.strip()
        # Handle explicit EDGES section or '#' separator
        if line == "EDGES" or line == "#":
            in_edges_section = True
            continue
        if line.startswith("SEPCO") or line.startswith("CLUSTERS"):
            in_edges_section = False
            continue
        if in_edges_section and line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    src = int(parts[0])
                    dst = int(parts[1])
                    nx_graph.add_edge(src, dst)
                except ValueError:
                    continue


def from_networkx(
    nx_graph,
    node_width: float = 20.0,
    node_height: float = 20.0,
    use_positions: bool = True,
) -> Graph:
    """Create a hola_graph Graph from a NetworkX graph.

    Requires networkx to be installed.

    Args:
        nx_graph: A NetworkX graph.
        node_width: Default width for nodes (must be positive).
        node_height: Default height for nodes (must be positive).
        use_positions: If True, use 'pos' attribute from nodes if available.

    Returns:
        A hola_graph Graph with the same structure.

    Raises:
        ImportError: If networkx is not installed.
        ValueError: If node dimensions are not positive.

    Example:
        >>> import networkx as nx
        >>> import hola_graph_utils as pu
        >>> nx_graph = nx.karate_club_graph()
        >>> g = pu.from_networkx(nx_graph)
        >>> do_hola(g)
    """
    try:
        import networkx as nx  # noqa: F401
    except ImportError as err:
        raise ImportError(
            "NetworkX is required for this function. "
            "Install it with: pip install networkx"
        ) from err

    # Validate default dimensions
    validate_dimensions(node_width, node_height, context="from_networkx defaults")

    g = Graph()
    node_map = {}  # Map from nx node ID to hola_graph Node

    # Add nodes
    for nx_node in nx_graph.nodes():
        attrs = nx_graph.nodes[nx_node]

        # Get dimensions from attributes or use defaults
        w = attrs.get("width", node_width)
        h = attrs.get("height", node_height)
        validate_dimensions(w, h, context=f"from_networkx node {nx_node}")

        # Check for position
        if use_positions and "pos" in attrs:
            pos = attrs["pos"]
            node = Node.allocate(pos[0], pos[1], w, h)
        else:
            node = Node.allocate(w, h)

        node.set_external_id(
            int(nx_node)
            if isinstance(nx_node, (int, float))
            else hash(nx_node) % (2**31)
        )
        g.add_node(node)
        node_map[nx_node] = node

    # Add edges
    for src, dst in nx_graph.edges():
        g.add_edge(node_map[src], node_map[dst])

    return g


def layout_networkx(
    nx_graph,
    opts: _core.HolaOpts | None = None,
    node_width: float = 20.0,
    node_height: float = 20.0,
) -> dict:
    """Apply HOLA layout to a NetworkX graph and return positions.

    This is a convenience function that converts to hola_graph, applies layout,
    and returns the positions in NetworkX-compatible format.

    Args:
        nx_graph: A NetworkX graph.
        opts: Optional HolaOpts for layout configuration.
        node_width: Default width for nodes (must be positive).
        node_height: Default height for nodes (must be positive).

    Returns:
        Dictionary mapping node IDs to (x, y) positions.

    Raises:
        ValueError: If node dimensions are not positive.

    Example:
        >>> import networkx as nx
        >>> import hola_graph_utils as pu
        >>> G = nx.karate_club_graph()
        >>> pos = pu.layout_networkx(G)
        >>> nx.draw(G, pos=pos)
    """
    # Convert to hola_graph
    g = from_networkx(nx_graph, node_width, node_height, use_positions=False)

    # Apply layout
    apply_hola(g, opts)

    # Extract positions
    positions = {}
    node_list = list(nx_graph.nodes())

    # Match by order (since we added nodes in the same order)
    hola_graph_nodes = g.get_nodes()
    for i, hola_graph_node in enumerate(hola_graph_nodes):
        if i < len(node_list):
            nx_node = node_list[i]
            centre = hola_graph_node.get_centre()
            positions[nx_node] = (centre.x, centre.y)

    return positions


# =============================================================================
# JSON Import/Export
# =============================================================================


def to_json(graph: Graph, indent: int | None = 2) -> str:
    """Export a hola_graph Graph to JSON format.

    The JSON format includes nodes with their positions and dimensions,
    and edges with source/target node IDs.

    Args:
        graph: The hola_graph Graph to export.
        indent: Indentation level for pretty printing. None for compact output.

    Returns:
        JSON string representation of the graph.

    Example:
        >>> g = Graph()
        >>> n1 = Node.allocate(10, 20)
        >>> n2 = Node.allocate(15, 25)
        >>> g.add_node(n1)
        >>> g.add_node(n2)
        >>> g.add_edge(n1, n2)
        >>> json_str = to_json(g)
        >>> print(json_str)
    """
    data: dict[str, Any] = {
        "nodes": [],
        "edges": [],
        "metadata": {
            "num_nodes": graph.get_num_nodes(),
            "num_edges": graph.get_num_edges(),
        },
    }

    # Export nodes
    for node in graph.get_nodes():
        centre = node.get_centre()
        dims = node.get_dimensions()
        node_data = {
            "id": node.id,
            "x": centre.x,
            "y": centre.y,
            "width": dims[0],
            "height": dims[1],
        }
        # Include external ID if set (only positive values)
        try:
            ext_id = node.get_external_id()
            if ext_id > 0:
                node_data["external_id"] = ext_id
        except Exception:
            pass

        data["nodes"].append(node_data)

    # Export edges by parsing TGLF (since edge iteration isn't directly exposed)
    tglf = graph.to_tglf()
    edges = _parse_tglf_edges_list(tglf)
    data["edges"] = edges

    return json.dumps(data, indent=indent)


def _parse_tglf_edges_list(tglf_content: str) -> list[dict[str, int]]:
    """Parse edges from TGLF content and return as list of dicts.

    TGLF format has nodes first, then edges after a '#' separator,
    or can have explicit EDGES section.

    Args:
        tglf_content: TGLF file content as string.

    Returns:
        List of edge dictionaries with 'source' and 'target' keys.
    """
    edges = []
    in_edges_section = False

    for line in tglf_content.split("\n"):
        line = line.strip()
        # Handle explicit EDGES section or '#' separator
        if line == "EDGES" or line == "#":
            in_edges_section = True
            continue
        if line.startswith("SEPCO") or line.startswith("CLUSTERS"):
            in_edges_section = False
            continue
        if in_edges_section and line and not line.startswith("#"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    src = int(parts[0])
                    dst = int(parts[1])
                    edges.append({"source": src, "target": dst})
                except ValueError:
                    continue

    return edges


def from_json(json_data: str | dict[str, Any], apply_positions: bool = True) -> Graph:
    """Create a hola_graph Graph from JSON data.

    Args:
        json_data: JSON string or dictionary with graph data.
        apply_positions: If True, set node positions from JSON data.

    Returns:
        A new hola_graph Graph.

    Raises:
        ValueError: If JSON data is invalid or missing required fields.

    Example:
        >>> json_str = '{"nodes": [{"id": 0, "x": 0, "y": 0, "width": 10, "height": 20}], "edges": []}'
        >>> g = from_json(json_str)
        >>> len(g)
        1
    """
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    if "nodes" not in data:
        raise ValueError("JSON data must contain 'nodes' field")

    g = Graph()
    node_map: dict[int, Node] = {}  # Map from JSON id to Node

    # Create nodes
    for node_data in data["nodes"]:
        if "width" not in node_data or "height" not in node_data:
            raise ValueError(f"Node missing width/height: {node_data}")

        w = float(node_data["width"])
        h = float(node_data["height"])
        node_id = node_data.get("id", "unknown")
        validate_dimensions(w, h, context=f"from_json node {node_id}")

        if apply_positions and "x" in node_data and "y" in node_data:
            x = float(node_data["x"])
            y = float(node_data["y"])
            node = Node.allocate(x, y, w, h)
        else:
            node = Node.allocate(w, h)

        # Set external ID if provided and valid (must be positive)
        if "external_id" in node_data:
            ext_id = int(node_data["external_id"])
            if ext_id >= 0:
                node.set_external_id(ext_id)

        g.add_node(node)

        # Map by JSON id if provided, otherwise by internal id
        json_id = node_data.get("id", node.id)
        node_map[json_id] = node

    # Create edges
    for edge_data in data.get("edges", []):
        src_id = edge_data.get("source")
        dst_id = edge_data.get("target")

        if src_id is None or dst_id is None:
            continue

        if src_id in node_map and dst_id in node_map:
            g.add_edge(node_map[src_id], node_map[dst_id])

    return g


def save_json(graph: Graph, path: str | Path, indent: int | None = 2) -> None:
    """Save a graph to a JSON file.

    Args:
        graph: The graph to save.
        path: Output path for the JSON file.
        indent: Indentation level for pretty printing.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(to_json(graph, indent=indent))


def load_json(path: str | Path, apply_positions: bool = True) -> Graph:
    """Load a graph from a JSON file.

    Args:
        path: Path to the JSON file.
        apply_positions: If True, set node positions from JSON data.

    Returns:
        The loaded Graph.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a .json file.
    """
    validated_path = validate_path(path, must_exist=True, expected_suffix=".json")

    with open(validated_path) as f:
        return from_json(f.read(), apply_positions=apply_positions)


# =============================================================================
# Matplotlib Visualization
# =============================================================================


def plot_graph(
    graph: Graph,
    ax=None,
    show_node_ids: bool = True,
    node_color: str = "lightblue",
    node_edge_color: str = "black",
    edge_color: str = "gray",
    node_alpha: float = 0.8,
    edge_alpha: float = 0.6,
    edge_width: float = 1.5,
    font_size: int = 10,
    title: str | None = None,
    figsize: tuple[float, float] = (10, 8),
):
    """Plot a hola_graph Graph using matplotlib.

    Renders nodes as rectangles with their actual dimensions and edges as
    lines connecting node centers.

    Args:
        graph: The hola_graph Graph to plot.
        ax: Optional matplotlib Axes to plot on. If None, creates new figure.
        show_node_ids: If True, display node IDs as labels.
        node_color: Fill color for nodes.
        node_edge_color: Border color for nodes.
        edge_color: Color for edges.
        node_alpha: Transparency for nodes (0-1).
        edge_alpha: Transparency for edges (0-1).
        edge_width: Line width for edges.
        font_size: Font size for node labels.
        title: Optional title for the plot.
        figsize: Figure size as (width, height) if creating new figure.

    Returns:
        The matplotlib Axes object.

    Raises:
        ImportError: If matplotlib is not installed.

    Example:
        >>> import hola_graph_utils as pu
        >>> g = pu.load_graph("graph.tglf")
        >>> do_hola(g)
        >>> ax = pu.plot_graph(g, title="My Graph")
        >>> import matplotlib.pyplot as plt
        >>> plt.show()
    """
    try:
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        from matplotlib.patches import FancyBboxPatch
    except ImportError as err:
        raise ImportError(
            "Matplotlib is required for this function. "
            "Install it with: pip install matplotlib"
        ) from err

    # Create figure and axes if not provided
    if ax is None:
        _, ax = plt.subplots(figsize=figsize)

    if graph.is_empty():
        ax.text(
            0.5,
            0.5,
            "Empty Graph",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=14,
        )
        if title:
            ax.set_title(title)
        return ax

    # Collect node data
    nodes_data = []
    for node in graph.get_nodes():
        centre = node.get_centre()
        dims = node.get_dimensions()
        nodes_data.append(
            {
                "id": node.id,
                "x": centre.x,
                "y": centre.y,
                "width": dims[0],
                "height": dims[1],
            }
        )

    # Get edges from TGLF
    tglf = graph.to_tglf()
    edges_list = _parse_tglf_edges_list(tglf)

    # Build node lookup for edge drawing
    node_lookup = {n["id"]: n for n in nodes_data}

    # Draw edges first (so nodes appear on top)
    edge_lines = []
    for edge in edges_list:
        src_id = edge["source"]
        dst_id = edge["target"]
        if src_id in node_lookup and dst_id in node_lookup:
            src = node_lookup[src_id]
            dst = node_lookup[dst_id]
            edge_lines.append([(src["x"], src["y"]), (dst["x"], dst["y"])])

    if edge_lines:
        lc = LineCollection(
            edge_lines, colors=edge_color, alpha=edge_alpha, linewidths=edge_width
        )
        ax.add_collection(lc)

    # Draw nodes as rectangles
    for node_data in nodes_data:
        x = node_data["x"] - node_data["width"] / 2
        y = node_data["y"] - node_data["height"] / 2
        rect = FancyBboxPatch(
            (x, y),
            node_data["width"],
            node_data["height"],
            boxstyle="round,pad=0.02,rounding_size=2",
            facecolor=node_color,
            edgecolor=node_edge_color,
            alpha=node_alpha,
            linewidth=1.5,
        )
        ax.add_patch(rect)

        # Add node ID label
        if show_node_ids:
            ax.text(
                node_data["x"],
                node_data["y"],
                str(node_data["id"]),
                ha="center",
                va="center",
                fontsize=font_size,
                fontweight="bold",
            )

    # Set axis limits with padding
    if nodes_data:
        all_x = [n["x"] for n in nodes_data]
        all_y = [n["y"] for n in nodes_data]
        max_dim = max(
            max(n["width"] for n in nodes_data), max(n["height"] for n in nodes_data)
        )
        padding = max_dim * 1.5

        ax.set_xlim(min(all_x) - padding, max(all_x) + padding)
        ax.set_ylim(min(all_y) - padding, max(all_y) + padding)

    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)

    if title:
        ax.set_title(title)

    return ax


def save_plot(graph: Graph, path: str | Path, dpi: int = 150, **kwargs) -> None:
    """Save a graph visualization to an image file.

    Args:
        graph: The hola_graph Graph to plot.
        path: Output path for the image file (supports png, pdf, svg, etc.).
        dpi: Resolution in dots per inch.
        **kwargs: Additional arguments passed to plot_graph().

    Raises:
        ImportError: If matplotlib is not installed.

    Example:
        >>> import hola_graph_utils as pu
        >>> g = pu.load_graph("graph.tglf")
        >>> do_hola(g)
        >>> pu.save_plot(g, "output.png", title="My Graph")
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as err:
        raise ImportError(
            "Matplotlib is required for this function. "
            "Install it with: pip install matplotlib"
        ) from err

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=kwargs.pop("figsize", (10, 8)))
    plot_graph(graph, ax=ax, **kwargs)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def plot_comparison(
    graph1: Graph,
    graph2: Graph,
    titles: tuple[str, str] = ("Before", "After"),
    figsize: tuple[float, float] = (16, 7),
    **kwargs,
):
    """Plot two graphs side by side for comparison.

    Useful for comparing a graph before and after layout.

    Args:
        graph1: First graph to plot.
        graph2: Second graph to plot.
        titles: Tuple of titles for each subplot.
        figsize: Figure size as (width, height).
        **kwargs: Additional arguments passed to plot_graph().

    Returns:
        Tuple of (fig, (ax1, ax2)).

    Raises:
        ImportError: If matplotlib is not installed.

    Example:
        >>> import hola_graph_utils as pu
        >>> g = pu.load_graph("graph.tglf")
        >>> # Save original positions
        >>> g.push_node_positions()
        >>> original = g  # Before layout
        >>> do_hola(g)
        >>> # Compare layouts (note: same graph object, positions changed)
        >>> fig, (ax1, ax2) = pu.plot_comparison(original, g)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as err:
        raise ImportError(
            "Matplotlib is required for this function. "
            "Install it with: pip install matplotlib"
        ) from err

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    plot_graph(graph1, ax=ax1, title=titles[0], **kwargs)
    plot_graph(graph2, ax=ax2, title=titles[1], **kwargs)

    fig.tight_layout()
    return fig, (ax1, ax2)
