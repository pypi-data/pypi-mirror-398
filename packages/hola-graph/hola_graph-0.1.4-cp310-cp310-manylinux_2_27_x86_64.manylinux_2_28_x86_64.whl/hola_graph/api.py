"""High-level Pythonic API for hola_graph.

This module provides a clean, Pythonic interface for creating and manipulating
graphs with the HOLA (Human-like Orthogonal Layout Algorithm).

Example:
    >>> from hola_graph.api import HolaGraph
    >>> g = HolaGraph()
    >>> a = g.add_node(30, 20, label="A")
    >>> b = g.add_node(30, 20, label="B")
    >>> g.connect(a, b)
    >>> g.layout()
    >>> g.to_svg("output.svg")
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from hola_graph._core import (
    Graph,
    HolaOpts,
    Node,
    do_hola,
    graph_from_tglf_file,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# HolaEdge - Simple edge representation
# =============================================================================


@dataclass(frozen=True)
class HolaEdge:
    """A simple, immutable representation of an edge.

    Attributes:
        source: The source node.
        target: The target node.
        id: The internal edge ID.
    """

    source: HolaNode
    target: HolaNode
    id: int

    def __repr__(self) -> str:
        src = self.source.label or self.source.id
        tgt = self.target.label or self.target.id
        return f"HolaEdge({src!r} -> {tgt!r})"


# =============================================================================
# HolaNode - Pythonic node wrapper
# =============================================================================


class HolaNode:
    """A Pythonic wrapper around the C++ Node class.

    Provides property-based access to node attributes and hides the
    C++ allocator pattern.

    Attributes:
        label: Optional string label for the node.

    Example:
        >>> node = HolaNode(30, 20, label="A")
        >>> print(node.position)
        (0.0, 0.0)
        >>> node.position = (50, 100)
        >>> print(node.size)
        (30.0, 20.0)
    """

    def __init__(
        self,
        width: float,
        height: float,
        x: float | None = None,
        y: float | None = None,
        label: str | None = None,
        _node: Node | None = None,
    ) -> None:
        """Create a new node.

        Args:
            width: Node width (must be positive).
            height: Node height (must be positive).
            x: Optional x position.
            y: Optional y position.
            label: Optional string label for referencing the node.
            _node: Internal use only - wrap an existing C++ Node.
        """
        if _node is not None:
            self._node = _node
        elif x is not None and y is not None:
            self._node = Node.allocate(x, y, width, height)
        else:
            self._node = Node.allocate(width, height)

        self._label = label

    @classmethod
    def _wrap(cls, node: Node, label: str | None = None) -> HolaNode:
        """Wrap an existing C++ Node object."""
        # Get dimensions from the node
        dims = node.get_dimensions()
        wrapper = cls(dims[0], dims[1], _node=node)
        wrapper._label = label
        return wrapper

    @property
    def id(self) -> int:
        """The internal node ID (read-only)."""
        return self._node.id

    @property
    def label(self) -> str | None:
        """The optional string label for this node."""
        return self._label

    @label.setter
    def label(self, value: str | None) -> None:
        self._label = value

    @property
    def position(self) -> tuple[float, float]:
        """The (x, y) center position of the node."""
        centre = self._node.get_centre()
        return (centre.x, centre.y)

    @position.setter
    def position(self, value: tuple[float, float]) -> None:
        self._node.set_centre(value[0], value[1])

    @property
    def x(self) -> float:
        """The x coordinate of the node center."""
        return self._node.get_centre().x

    @x.setter
    def x(self, value: float) -> None:
        self._node.set_centre(value, self.y)

    @property
    def y(self) -> float:
        """The y coordinate of the node center."""
        return self._node.get_centre().y

    @y.setter
    def y(self, value: float) -> None:
        self._node.set_centre(self.x, value)

    @property
    def size(self) -> tuple[float, float]:
        """The (width, height) dimensions of the node."""
        dims = self._node.get_dimensions()
        return (dims[0], dims[1])

    @size.setter
    def size(self, value: tuple[float, float]) -> None:
        self._node.set_dims(value[0], value[1])

    @property
    def width(self) -> float:
        """The width of the node."""
        return self._node.get_dimensions()[0]

    @width.setter
    def width(self, value: float) -> None:
        self._node.set_dims(value, self.height)

    @property
    def height(self) -> float:
        """The height of the node."""
        return self._node.get_dimensions()[1]

    @height.setter
    def height(self, value: float) -> None:
        self._node.set_dims(self.width, value)

    @property
    def degree(self) -> int:
        """The number of edges connected to this node."""
        return self._node.get_degree()

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """The bounding box as (x_min, y_min, x_max, y_max)."""
        bb = self._node.get_bounding_box()
        return (bb.x, bb.y, bb.X, bb.Y)

    def translate(self, dx: float, dy: float) -> None:
        """Move the node by the given offset.

        Args:
            dx: Horizontal offset.
            dy: Vertical offset.
        """
        self._node.translate(dx, dy)

    def __repr__(self) -> str:
        label_str = f", label={self._label!r}" if self._label else ""
        return (
            f"HolaNode(id={self.id}, pos={self.position}, size={self.size}{label_str})"
        )

    def __str__(self) -> str:
        if self._label:
            return f"Node[{self._label}]"
        return f"Node[{self.id}]"


# =============================================================================
# HolaGraph - Pythonic graph wrapper
# =============================================================================


class HolaGraph:
    """A Pythonic wrapper around the C++ Graph class.

    Provides a clean, intuitive API for creating and manipulating graphs
    with the HOLA layout algorithm.

    Example:
        >>> g = HolaGraph()
        >>> a = g.add_node(30, 20, label="A")
        >>> b = g.add_node(30, 20, label="B")
        >>> g.connect(a, b)
        >>> g.layout()
        >>> print(g)
        HolaGraph(2 nodes, 1 edges)

        >>> # Dict-like access
        >>> node = g["A"]
        >>> "A" in g
        True

        >>> # Iteration
        >>> for node in g.nodes:
        ...     print(node.label, node.position)
    """

    def __init__(self, _graph: Graph | None = None) -> None:
        """Create a new empty graph.

        Args:
            _graph: Internal use only - wrap an existing C++ Graph.
        """
        self._graph = _graph if _graph is not None else Graph()
        self._nodes_by_label: dict[str, HolaNode] = {}
        self._nodes_by_id: dict[int, HolaNode] = {}
        self._label_counter = 0

    def _generate_label(self) -> str:
        """Generate a unique label for a node."""
        while True:
            label = f"n{self._label_counter}"
            self._label_counter += 1
            if label not in self._nodes_by_label:
                return label

    # -------------------------------------------------------------------------
    # Node management
    # -------------------------------------------------------------------------

    def add_node(
        self,
        width: float,
        height: float,
        x: float | None = None,
        y: float | None = None,
        label: str | None = None,
    ) -> HolaNode:
        """Add a node to the graph.

        Args:
            width: Node width (must be positive).
            height: Node height (must be positive).
            x: Optional x position.
            y: Optional y position.
            label: Optional label. Auto-generated if not provided.

        Returns:
            The created node.

        Raises:
            ValueError: If width or height is not positive.
            ValueError: If label already exists.

        Example:
            >>> g = HolaGraph()
            >>> a = g.add_node(30, 20, label="A")
            >>> b = g.add_node(30, 20, x=100, y=50)
            >>> g.connect(a, b)
        """
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Dimensions must be positive: width={width}, height={height}"
            )

        if label is None:
            label = self._generate_label()
        elif label in self._nodes_by_label:
            raise ValueError(f"Node with label {label!r} already exists")

        node = HolaNode(width, height, x, y, label=label)
        self._graph.add_node(node._node)
        self._nodes_by_label[label] = node
        self._nodes_by_id[node.id] = node

        return node

    def node(self, label: str) -> HolaNode:
        """Get a node by label.

        Args:
            label: The node label.

        Returns:
            The node with the given label.

        Raises:
            KeyError: If no node with that label exists.
        """
        if label not in self._nodes_by_label:
            raise KeyError(f"No node with label {label!r}")
        return self._nodes_by_label[label]

    def remove_node(self, node: str | HolaNode) -> None:
        """Remove a node and all its edges from the graph.

        Args:
            node: The node label or HolaNode object.

        Raises:
            KeyError: If the node doesn't exist.
        """
        if isinstance(node, str):
            if node not in self._nodes_by_label:
                raise KeyError(f"No node with label {node!r}")
            hola_node = self._nodes_by_label[node]
        else:
            hola_node = node

        self._graph.sever_remove_node(hola_node._node.id)

        if hola_node.label and hola_node.label in self._nodes_by_label:
            del self._nodes_by_label[hola_node.label]
        if hola_node.id in self._nodes_by_id:
            del self._nodes_by_id[hola_node.id]

    @property
    def nodes(self) -> list[HolaNode]:
        """List of all nodes in the graph."""
        return list(self._nodes_by_id.values())

    # -------------------------------------------------------------------------
    # Edge management
    # -------------------------------------------------------------------------

    @overload
    def connect(self, source: str, target: str) -> None: ...

    @overload
    def connect(self, source: HolaNode, target: HolaNode) -> None: ...

    def connect(self, source: str | HolaNode, target: str | HolaNode) -> None:
        """Connect two nodes with an edge.

        Args:
            source: Source node (label or HolaNode).
            target: Target node (label or HolaNode).

        Raises:
            KeyError: If a node label doesn't exist.

        Example:
            >>> g.connect("A", "B")
            >>> g.connect(node_a, node_b)
        """
        src_node = self._resolve_node(source)
        tgt_node = self._resolve_node(target)

        self._graph.add_edge(src_node._node, tgt_node._node)

    def _resolve_node(self, node: str | HolaNode) -> HolaNode:
        """Resolve a node reference to a HolaNode."""
        if isinstance(node, str):
            if node not in self._nodes_by_label:
                raise KeyError(f"No node with label {node!r}")
            return self._nodes_by_label[node]
        return node

    @property
    def edges(self) -> list[HolaEdge]:
        """List of all edges in the graph.

        Note: Parses TGLF output since edge iteration isn't directly exposed.
        """
        edges = []
        seen_edges: set[tuple[int, int]] = set()
        tglf = self._graph.to_tglf()

        # Parse edges from TGLF
        # Format: nodes section, then # separator, then edges section, then # separator, then constraints
        lines = tglf.split("\n")
        in_edges = False
        edge_id = 0

        for line in lines:
            line = line.strip()

            # First # starts edge section
            if line == "#" and not in_edges:
                in_edges = True
                continue

            # Second # ends edge section (starts constraints)
            if line == "#" and in_edges:
                break

            if in_edges and line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        src_id = int(parts[0])
                        tgt_id = int(parts[1])
                        edge_key = (min(src_id, tgt_id), max(src_id, tgt_id))

                        if edge_key not in seen_edges:
                            if (
                                src_id in self._nodes_by_id
                                and tgt_id in self._nodes_by_id
                            ):
                                edges.append(
                                    HolaEdge(
                                        source=self._nodes_by_id[src_id],
                                        target=self._nodes_by_id[tgt_id],
                                        id=edge_id,
                                    )
                                )
                                seen_edges.add(edge_key)
                                edge_id += 1
                    except ValueError:
                        continue

        return edges

    # -------------------------------------------------------------------------
    # Layout
    # -------------------------------------------------------------------------

    def layout(self, opts: HolaOpts | None = None) -> None:
        """Apply the HOLA layout algorithm.

        Args:
            opts: Optional layout options.

        Example:
            >>> g.layout()
            >>> # Or with options:
            >>> opts = HolaOpts()
            >>> opts.nodePaddingScalar = 2.0
            >>> g.layout(opts)
        """
        if opts is not None:
            do_hola(self._graph, opts)
        else:
            do_hola(self._graph)

    def destress(self) -> None:
        """Reduce stress via gradient-descent optimization."""
        self._graph.destress()

    def rotate(self, degrees: int) -> None:
        """Rotate the layout.

        Args:
            degrees: Rotation angle. Must be 90, -90, or 180.

        Raises:
            ValueError: If degrees is not 90, -90, or 180.
        """
        if degrees == 90:
            self._graph.rotate_90cw()
        elif degrees == -90:
            self._graph.rotate_90acw()
        elif degrees == 180:
            self._graph.rotate_180()
        else:
            raise ValueError(f"Rotation must be 90, -90, or 180 degrees, got {degrees}")

    def translate(self, dx: float, dy: float) -> None:
        """Translate the entire layout.

        Args:
            dx: Horizontal offset.
            dy: Vertical offset.
        """
        self._graph.translate(dx, dy)

    # -------------------------------------------------------------------------
    # Graph properties
    # -------------------------------------------------------------------------

    @property
    def num_nodes(self) -> int:
        """Number of nodes in the graph."""
        return self._graph.get_num_nodes()

    @property
    def num_edges(self) -> int:
        """Number of edges in the graph."""
        return self._graph.get_num_edges()

    @property
    def is_empty(self) -> bool:
        """Whether the graph has no nodes."""
        return self._graph.is_empty()

    @property
    def is_tree(self) -> bool:
        """Whether the graph is a tree."""
        return self._graph.is_tree()

    @property
    def max_degree(self) -> int:
        """Maximum degree of any node."""
        return self._graph.get_max_degree()

    # -------------------------------------------------------------------------
    # Dict-like access
    # -------------------------------------------------------------------------

    def __getitem__(self, label: str) -> HolaNode:
        """Get a node by label using bracket notation.

        Example:
            >>> node = g["A"]
        """
        return self.node(label)

    def __contains__(self, item: str | HolaNode) -> bool:
        """Check if a node exists in the graph.

        Example:
            >>> "A" in g
            True
        """
        if isinstance(item, str):
            return item in self._nodes_by_label
        return item.id in self._nodes_by_id

    def __len__(self) -> int:
        """Return the number of nodes."""
        return self.num_nodes

    def __iter__(self) -> Iterator[HolaNode]:
        """Iterate over all nodes."""
        return iter(self.nodes)

    def __repr__(self) -> str:
        return f"HolaGraph({self.num_nodes} nodes, {self.num_edges} edges)"

    def __str__(self) -> str:
        return self.__repr__()

    # -------------------------------------------------------------------------
    # Export methods
    # -------------------------------------------------------------------------

    def to_svg(self, path: str | Path | None = None) -> str:
        """Export the graph to SVG format.

        Args:
            path: Optional file path to save the SVG.

        Returns:
            The SVG content as a string.
        """
        svg = self._graph.to_svg()
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(svg)
        return svg

    def to_tglf(self, path: str | Path | None = None) -> str:
        """Export the graph to TGLF format.

        Args:
            path: Optional file path to save the TGLF.

        Returns:
            The TGLF content as a string.
        """
        tglf = self._graph.to_tglf()
        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(tglf)
        return tglf

    def to_json(self, path: str | Path | None = None, indent: int = 2) -> str:
        """Export the graph to JSON format.

        Args:
            path: Optional file path to save the JSON.
            indent: Indentation level for pretty printing.

        Returns:
            The JSON content as a string.
        """
        data: dict[str, Any] = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "num_nodes": self.num_nodes,
                "num_edges": self.num_edges,
            },
        }

        for node in self.nodes:
            node_data: dict[str, Any] = {
                "id": node.id,
                "label": node.label,
                "x": node.x,
                "y": node.y,
                "width": node.width,
                "height": node.height,
            }
            data["nodes"].append(node_data)

        for edge in self.edges:
            edge_data = {
                "source": edge.source.label,
                "target": edge.target.label,
                "source_id": edge.source.id,
                "target_id": edge.target.id,
            }
            data["edges"].append(edge_data)

        json_str = json.dumps(data, indent=indent)

        if path is not None:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json_str)

        return json_str

    def to_networkx(self, include_positions: bool = True):
        """Convert to a NetworkX graph.

        Requires networkx to be installed.

        Args:
            include_positions: Include node positions as 'pos' attribute.

        Returns:
            A networkx.Graph object.

        Raises:
            ImportError: If networkx is not installed.
        """
        try:
            import networkx as nx
        except ImportError as err:
            raise ImportError(
                "NetworkX is required. Install with: pip install networkx"
            ) from err

        G = nx.Graph()

        for node in self.nodes:
            attrs: dict[str, Any] = {
                "label": node.label,
                "width": node.width,
                "height": node.height,
            }
            if include_positions:
                attrs["pos"] = node.position
            G.add_node(node.label, **attrs)

        for edge in self.edges:
            G.add_edge(edge.source.label, edge.target.label)

        return G

    # -------------------------------------------------------------------------
    # Class methods for loading
    # -------------------------------------------------------------------------

    @classmethod
    def from_tglf(cls, path: str | Path) -> HolaGraph:
        """Load a graph from a TGLF file.

        Args:
            path: Path to the TGLF file.

        Returns:
            A new HolaGraph.

        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        cpp_graph = graph_from_tglf_file(str(path))
        hola_graph = cls(_graph=cpp_graph)

        # Wrap existing nodes
        for cpp_node in cpp_graph.get_nodes():
            label = hola_graph._generate_label()
            node = HolaNode._wrap(cpp_node, label=label)
            hola_graph._nodes_by_label[label] = node
            hola_graph._nodes_by_id[node.id] = node

        return hola_graph

    @classmethod
    def from_json(cls, path_or_data: str | Path | dict) -> HolaGraph:
        """Load a graph from JSON.

        Args:
            path_or_data: Path to JSON file, JSON string, or dict.

        Returns:
            A new HolaGraph.
        """
        if isinstance(path_or_data, dict):
            data = path_or_data
        elif isinstance(path_or_data, Path) or (
            isinstance(path_or_data, str) and Path(path_or_data).exists()
        ):
            path = Path(path_or_data)
            data = json.loads(path.read_text())
        else:
            data = json.loads(path_or_data)

        g = cls()

        # Create nodes
        node_map: dict[str | int, str] = {}  # old id/label -> new label
        for node_data in data.get("nodes", []):
            label = node_data.get("label") or g._generate_label()
            x = node_data.get("x")
            y = node_data.get("y")
            width = node_data.get("width", 20.0)
            height = node_data.get("height", 20.0)

            g.add_node(width, height, x=x, y=y, label=label)

            # Map old identifiers to new label
            if "id" in node_data:
                node_map[node_data["id"]] = label
            if "label" in node_data:
                node_map[node_data["label"]] = label

        # Create edges
        for edge_data in data.get("edges", []):
            src = edge_data.get("source") or edge_data.get("source_id")
            tgt = edge_data.get("target") or edge_data.get("target_id")

            if src in node_map and tgt in node_map:
                g.connect(node_map[src], node_map[tgt])

        return g

    @classmethod
    def from_networkx(
        cls,
        nx_graph,
        node_width: float = 20.0,
        node_height: float = 20.0,
        use_positions: bool = True,
    ) -> HolaGraph:
        """Create from a NetworkX graph.

        Requires networkx to be installed.

        Args:
            nx_graph: A NetworkX graph.
            node_width: Default node width.
            node_height: Default node height.
            use_positions: Use 'pos' attribute if available.

        Returns:
            A new HolaGraph.

        Raises:
            ImportError: If networkx is not installed.
        """
        try:
            import networkx as nx  # noqa: F401
        except ImportError as err:
            raise ImportError(
                "NetworkX is required. Install with: pip install networkx"
            ) from err

        g = cls()
        node_map: dict[Any, str] = {}

        # Add nodes
        for nx_node in nx_graph.nodes():
            attrs = nx_graph.nodes[nx_node]
            label = str(nx_node)
            width = attrs.get("width", node_width)
            height = attrs.get("height", node_height)

            x, y = None, None
            if use_positions and "pos" in attrs:
                x, y = attrs["pos"]

            g.add_node(width, height, x=x, y=y, label=label)
            node_map[nx_node] = label

        # Add edges
        for src, tgt in nx_graph.edges():
            g.connect(node_map[src], node_map[tgt])

        return g

    # -------------------------------------------------------------------------
    # Context manager for position saving
    # -------------------------------------------------------------------------

    def save_positions(self) -> None:
        """Save current node positions to internal stack.

        Use with restore_positions() to experiment with layouts.
        """
        self._graph.push_node_positions()

    def restore_positions(self) -> None:
        """Restore node positions from internal stack."""
        self._graph.pop_node_positions()

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self._graph.clear()
        self._nodes_by_label.clear()
        self._nodes_by_id.clear()

    # -------------------------------------------------------------------------
    # Access to underlying C++ graph
    # -------------------------------------------------------------------------

    @property
    def _raw(self) -> Graph:
        """Access the underlying C++ Graph object.

        For advanced use cases that need direct access to the C++ API.
        """
        return self._graph
