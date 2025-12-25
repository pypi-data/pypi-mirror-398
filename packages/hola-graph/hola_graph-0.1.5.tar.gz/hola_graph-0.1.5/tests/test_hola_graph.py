"""Comprehensive test suite for hola-graph."""

import os
import sys
from os.path import exists, join

import pytest

PARENT_DIR = os.path.dirname(__file__)
BUILD_DIR = join(os.path.dirname(PARENT_DIR), "build")
OUTPUTS_DIR = join(BUILD_DIR, "test-outputs")

try:
    import hola_graph  # noqa: F401
except ImportError:
    # assumes hola_graph has just been built in the project directory
    sys.path.insert(0, BUILD_DIR)

from hola_graph._core import (  # noqa: E402
    Edge,
    Graph,
    Node,
    do_hola,
    graph_from_tglf_file,
)


def output(g, name):
    """Helper to write graph outputs for visual inspection."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    tglf = f"{OUTPUTS_DIR}/{name}.tglf"
    svg = f"{OUTPUTS_DIR}/{name}.svg"
    with open(tglf, "w") as f:
        f.write(g.to_tglf())
    assert exists(tglf)
    with open(svg, "w") as f:
        f.write(g.to_svg())
    assert exists(svg)


def get_test_graph():
    """Load the standard test graph."""
    return graph_from_tglf_file(os.path.join(PARENT_DIR, "test_graph.tglf"))


# =============================================================================
# Basic Graph Tests
# =============================================================================


class TestGraph:
    """Tests for Graph class."""

    def test_empty_graph(self):
        """Test empty graph creation."""
        g = Graph()
        assert g.get_num_nodes() == 0
        assert g.get_num_edges() == 0
        assert g.is_empty()

    def test_graph_from_tglf_file(self):
        """Test loading graph from TGLF file."""
        g = get_test_graph()
        assert g.get_num_nodes() == 30
        assert g.get_num_edges() == 33
        assert not g.is_empty()

    def test_graph_repr(self):
        """Test Graph.__repr__ method."""
        g = Graph()
        repr_str = repr(g)
        assert "hola_graph.Graph" in repr_str
        assert "0 nodes" in repr_str
        assert "0 edges" in repr_str

        g = get_test_graph()
        repr_str = repr(g)
        assert "30 nodes" in repr_str
        assert "33 edges" in repr_str

    def test_graph_to_tglf(self):
        """Test TGLF serialization."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(n1, n2)

        tglf = g.to_tglf()
        assert isinstance(tglf, str)
        assert len(tglf) > 0

    def test_graph_to_svg(self):
        """Test SVG serialization."""
        g = get_test_graph()
        svg = g.to_svg()
        assert isinstance(svg, str)
        assert "<svg" in svg or "svg" in svg.lower()

    def test_graph_is_tree(self):
        """Test tree detection."""
        # Create a simple tree: A -> B -> C
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(10.0, 10.0)
        n3 = Node.allocate(10.0, 10.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)
        g.add_edge(n1, n2)
        g.add_edge(n2, n3)
        assert g.is_tree()

        # Add a cycle - no longer a tree
        g.add_edge(n3, n1)
        assert not g.is_tree()


# =============================================================================
# Node Tests
# =============================================================================


class TestNode:
    """Tests for Node class."""

    def test_node_allocate_dimensions(self):
        """Test Node allocation with width and height."""
        n = Node.allocate(10.2, 3.4)
        dims = n.get_dimensions()
        assert dims == (10.2, 3.4)

    def test_node_allocate_position(self):
        """Test Node allocation with position and dimensions."""
        n = Node.allocate(5.0, 10.0, 20.0, 30.0)  # x, y, w, h
        dims = n.get_dimensions()
        assert dims == (20.0, 30.0)

    def test_node_repr(self):
        """Test Node.__repr__ method."""
        n = Node.allocate(15.5, 25.5)
        repr_str = repr(n)
        assert "hola_graph.Node" in repr_str
        assert "id=" in repr_str
        assert "w=" in repr_str
        assert "h=" in repr_str

    def test_node_id(self):
        """Test that each node gets a unique ID."""
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(10.0, 10.0)
        assert n1.id != n2.id

    def test_node_set_centre(self):
        """Test setting node centre position."""
        g = Graph()
        n = Node.allocate(10.0, 10.0)
        g.add_node(n)
        n.set_centre(100.0, 200.0)
        centre = n.get_centre()
        assert centre.x == 100.0
        assert centre.y == 200.0

    def test_node_translate(self):
        """Test translating node position."""
        g = Graph()
        n = Node.allocate(10.0, 10.0)
        g.add_node(n)
        n.set_centre(0.0, 0.0)
        n.translate(50.0, 75.0)
        centre = n.get_centre()
        assert centre.x == 50.0
        assert centre.y == 75.0

    def test_node_set_dims(self):
        """Test setting node dimensions."""
        n = Node.allocate(10.0, 10.0)
        n.set_dims(30.0, 40.0)
        dims = n.get_dimensions()
        assert dims == (30.0, 40.0)

    def test_node_add_padding(self):
        """Test adding padding to node dimensions."""
        n = Node.allocate(10.0, 20.0)
        n.add_padding(5.0, 10.0)
        dims = n.get_dimensions()
        assert dims == (15.0, 30.0)

    def test_node_degree(self):
        """Test node degree (number of edges)."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(10.0, 10.0)
        n3 = Node.allocate(10.0, 10.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)

        assert n1.get_degree() == 0
        g.add_edge(n1, n2)
        assert n1.get_degree() == 1
        g.add_edge(n1, n3)
        assert n1.get_degree() == 2

    def test_node_is_root(self):
        """Test root node marking."""
        n = Node.allocate(10.0, 10.0)
        assert not n.is_root()
        n.set_is_root(True)
        assert n.is_root()
        n.set_is_root(False)
        assert not n.is_root()


# =============================================================================
# Edge Tests
# =============================================================================


class TestEdge:
    """Tests for Edge class."""

    def test_edge_creation(self):
        """Test edge creation between nodes."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        g.add_node(n1)
        g.add_node(n2)

        e = Edge.allocate(n1, n2)
        g.add_edge(e)

        assert g.get_num_edges() == 1

    def test_edge_add_directly(self):
        """Test adding edge directly from nodes."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(n1, n2)

        assert g.get_num_edges() == 1

    def test_edge_repr(self):
        """Test Edge.__repr__ method."""
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        e = Edge.allocate(n1, n2)
        repr_str = repr(e)
        assert "hola_graph.Edge" in repr_str
        assert "id=" in repr_str

    def test_edge_id(self):
        """Test that each edge gets a unique ID."""
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        n3 = Node.allocate(30.0, 30.0)

        e1 = Edge.allocate(n1, n2)
        e2 = Edge.allocate(n2, n3)

        assert e1.id() != e2.id()


# =============================================================================
# Layout Tests
# =============================================================================


class TestLayout:
    """Tests for layout operations."""

    def test_do_hola(self):
        """Test HOLA layout algorithm."""
        g = get_test_graph()
        output(g, "before")
        do_hola(g)
        output(g, "after")
        # Verify graph is still valid after layout
        assert g.get_num_nodes() == 30
        assert g.get_num_edges() == 33

    def test_graph_translate(self):
        """Test translating entire graph."""
        g = Graph()
        n = Node.allocate(10.0, 10.0)
        g.add_node(n)
        n.set_centre(0.0, 0.0)

        g.translate(100.0, 200.0)

        centre = n.get_centre()
        assert centre.x == 100.0
        assert centre.y == 200.0

    def test_graph_destress(self):
        """Test destress layout operation."""
        g = get_test_graph()
        # Should not raise
        g.destress()
        assert g.get_num_nodes() == 30


# =============================================================================
# Options Tests
# =============================================================================


class TestOptions:
    """Tests for layout options."""

    def test_hola_opts_creation(self):
        """Test HolaOpts creation."""
        from hola_graph._core import HolaOpts

        opts = HolaOpts()
        # Verify default values exist
        assert hasattr(opts, "preferConvexTrees")
        assert hasattr(opts, "nodePaddingScalar")

    def test_hola_opts_modification(self):
        """Test modifying HolaOpts."""
        from hola_graph._core import HolaOpts

        opts = HolaOpts()
        opts.nodePaddingScalar = 2.0
        assert opts.nodePaddingScalar == 2.0

    def test_cola_options_creation(self):
        """Test ColaOptions creation."""
        from hola_graph._core import ColaOptions

        opts = ColaOptions()
        assert hasattr(opts, "idealEdgeLength")
        assert hasattr(opts, "preventOverlaps")

    def test_do_hola_with_opts(self):
        """Test HOLA with custom options."""
        from hola_graph._core import HolaOpts

        g = get_test_graph()
        opts = HolaOpts()
        opts.nodePaddingScalar = 1.5
        do_hola(g, opts)
        assert g.get_num_nodes() == 30


# =============================================================================
# BoundingBox Tests
# =============================================================================


class TestBoundingBox:
    """Tests for BoundingBox class."""

    def test_bounding_box_creation(self):
        """Test BoundingBox creation."""
        from hola_graph._core import BoundingBox

        bb = BoundingBox(0.0, 100.0, 0.0, 50.0)
        assert bb.x == 0.0
        assert bb.X == 100.0
        assert bb.y == 0.0
        assert bb.Y == 50.0

    def test_bounding_box_dimensions(self):
        """Test BoundingBox width and height."""
        from hola_graph._core import BoundingBox

        bb = BoundingBox(0.0, 100.0, 0.0, 50.0)
        assert bb.w() == 100.0
        assert bb.h() == 50.0

    def test_node_bounding_box(self):
        """Test getting bounding box from node."""
        n = Node.allocate(20.0, 30.0)
        bb = n.get_bounding_box()
        assert bb.w() == 20.0
        assert bb.h() == 30.0


# =============================================================================
# Avoid Submodule Tests
# =============================================================================


class TestAvoidSubmodule:
    """Tests for the avoid submodule."""

    def test_point_creation(self):
        """Test Point creation."""
        from hola_graph._core import avoid

        p = avoid.Point(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_point_default(self):
        """Test Point default constructor."""
        from hola_graph._core import avoid

        p = avoid.Point()
        assert p.x == 0.0
        assert p.y == 0.0

    def test_point_equality(self):
        """Test Point equality comparison."""
        from hola_graph._core import avoid

        p1 = avoid.Point(10.0, 20.0)
        p2 = avoid.Point(10.0, 20.0)
        p3 = avoid.Point(10.0, 30.0)
        assert p1 == p2
        assert p1 != p3

    def test_point_arithmetic(self):
        """Test Point arithmetic operations."""
        from hola_graph._core import avoid

        p1 = avoid.Point(10.0, 20.0)
        p2 = avoid.Point(5.0, 10.0)

        p_add = p1 + p2
        assert p_add.x == 15.0
        assert p_add.y == 30.0

        p_sub = p1 - p2
        assert p_sub.x == 5.0
        assert p_sub.y == 10.0

    def test_box_creation(self):
        """Test Box creation."""
        from hola_graph._core import avoid

        b = avoid.Box()
        assert hasattr(b, "min")
        assert hasattr(b, "max")

    def test_rectangle_creation(self):
        """Test Rectangle creation."""
        from hola_graph._core import avoid

        tl = avoid.Point(0.0, 0.0)
        br = avoid.Point(100.0, 50.0)
        rect = avoid.Rectangle(tl, br)
        assert rect.size() == 4  # Rectangle has 4 corners


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_tglf_file(self):
        """Test that loading non-existent file raises error."""
        with pytest.raises(Exception):  # noqa: B017
            graph_from_tglf_file("/nonexistent/path/file.tglf")

    def test_has_node_false(self):
        """Test has_node returns False for non-existent node."""
        g = Graph()
        assert not g.has_node(9999)

    def test_has_edge_false(self):
        """Test has_edge returns False for non-existent edge."""
        g = Graph()
        assert not g.has_edge(9999)


# =============================================================================
# Graph Operations Tests
# =============================================================================


class TestGraphOperations:
    """Tests for graph operations."""

    def test_graph_max_degree(self):
        """Test getting maximum degree."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(10.0, 10.0)
        n3 = Node.allocate(10.0, 10.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)
        g.add_edge(n1, n2)
        g.add_edge(n1, n3)

        assert g.get_max_degree() == 2  # n1 has degree 2

    def test_graph_iel(self):
        """Test ideal edge length."""
        g = get_test_graph()
        iel = g.get_iel()
        assert iel > 0

    def test_graph_avg_node_dim(self):
        """Test average node dimension."""
        g = Graph()
        n1 = Node.allocate(10.0, 20.0)
        n2 = Node.allocate(30.0, 40.0)
        g.add_node(n1)
        g.add_node(n2)

        avg = g.compute_avg_node_dim()
        # Average of (10+20+30+40)/4 = 25
        assert avg == 25.0

    def test_push_pop_positions(self):
        """Test saving and restoring node positions."""
        g = Graph()
        n = Node.allocate(10.0, 10.0)
        g.add_node(n)
        n.set_centre(0.0, 0.0)

        g.push_node_positions()
        n.set_centre(100.0, 100.0)
        centre = n.get_centre()
        assert centre.x == 100.0
        assert centre.y == 100.0

        g.pop_node_positions()
        centre = n.get_centre()
        assert centre.x == 0.0
        assert centre.y == 0.0

    def test_edge_thickness(self):
        """Test edge thickness property."""
        g = Graph()
        g.set_edge_thickness(2.5)
        assert g.get_edge_thickness() == 2.5


# =============================================================================
# New Pythonic API Tests
# =============================================================================


class TestPythonicAPI:
    """Tests for new Pythonic API features."""

    def test_graph_len(self):
        """Test Graph.__len__ method."""
        g = Graph()
        assert len(g) == 0

        n1 = Node.allocate(10.0, 10.0)
        g.add_node(n1)
        assert len(g) == 1

        n2 = Node.allocate(20.0, 20.0)
        g.add_node(n2)
        assert len(g) == 2

    def test_graph_get_nodes(self):
        """Test Graph.get_nodes() method."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        n2 = Node.allocate(20.0, 20.0)
        n3 = Node.allocate(30.0, 30.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)

        nodes = g.get_nodes()
        assert len(nodes) == 3
        # Check that we got Node objects
        for node in nodes:
            assert hasattr(node, "id")
            assert hasattr(node, "get_dimensions")

    def test_graph_contains(self):
        """Test Graph.__contains__ method."""
        g = Graph()
        n1 = Node.allocate(10.0, 10.0)
        g.add_node(n1)

        assert n1.id in g
        assert 99999 not in g

    def test_get_nodes_after_layout(self):
        """Test that get_nodes() works after layout."""
        g = get_test_graph()
        do_hola(g)

        nodes = g.get_nodes()
        assert len(nodes) == 30
        # Verify positions are set
        for node in nodes:
            centre = node.get_centre()
            # After layout, positions should be defined
            assert hasattr(centre, "x")
            assert hasattr(centre, "y")


# =============================================================================
# Utilities Module Tests
# =============================================================================


class TestHolaGraphUtils:
    """Tests for hola_graph.utils module."""

    def test_load_graph(self):
        """Test load_graph function."""
        from hola_graph import utils as pu

        g = pu.load_graph(os.path.join(PARENT_DIR, "test_graph.tglf"))
        assert g.get_num_nodes() == 30

    def test_load_graph_file_not_found(self):
        """Test load_graph with missing file."""
        from hola_graph import utils as pu

        with pytest.raises(FileNotFoundError):
            pu.load_graph("/nonexistent/path.tglf")

    def test_load_graph_wrong_extension(self):
        """Test load_graph with wrong file extension."""
        import tempfile

        from hola_graph import utils as pu

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test")
            temp_path = f.name
        try:
            with pytest.raises(ValueError):
                pu.load_graph(temp_path)
        finally:
            os.unlink(temp_path)

    def test_graph_stats(self):
        """Test graph_stats function."""
        from hola_graph import utils as pu

        g = get_test_graph()
        stats = pu.graph_stats(g)

        assert stats["num_nodes"] == 30
        assert stats["num_edges"] == 33
        assert stats["is_empty"] is False
        assert "is_tree" in stats
        assert "max_degree" in stats
        assert "avg_node_dim" in stats

    def test_apply_hola_chaining(self):
        """Test apply_hola returns graph for chaining."""
        from hola_graph import utils as pu

        g = get_test_graph()
        result = pu.apply_hola(g)
        assert result is g

    def test_layout_context(self):
        """Test layout_context context manager."""
        from hola_graph import utils as pu

        g = Graph()
        n = Node.allocate(10.0, 10.0)
        g.add_node(n)
        n.set_centre(50.0, 50.0)

        original_x = n.get_centre().x
        original_y = n.get_centre().y

        with pu.layout_context(g):
            n.set_centre(100.0, 100.0)
            assert n.get_centre().x == 100.0

        # Position should be restored
        assert n.get_centre().x == original_x
        assert n.get_centre().y == original_y

    def test_graph_builder(self):
        """Test GraphBuilder class."""
        from hola_graph import utils as pu

        g = (
            pu.GraphBuilder()
            .add_node(10, 10, name="A")
            .add_node(20, 20, name="B")
            .add_node(15, 15, name="C")
            .add_edge("A", "B")
            .add_edge("B", "C")
            .build()
        )

        assert g.get_num_nodes() == 3
        assert g.get_num_edges() == 2

    def test_compact_layout_opts(self):
        """Test compact_layout_opts preset."""
        from hola_graph import utils as pu

        opts = pu.compact_layout_opts()
        assert opts.nodePaddingScalar == 0.5

    def test_spacious_layout_opts(self):
        """Test spacious_layout_opts preset."""
        from hola_graph import utils as pu

        opts = pu.spacious_layout_opts()
        assert opts.nodePaddingScalar == 2.0


# =============================================================================
# JSON Import/Export Tests
# =============================================================================


class TestJSONImportExport:
    """Tests for JSON import/export functionality."""

    def test_to_json_basic(self):
        """Test basic JSON export."""
        import json

        from hola_graph import utils as pu

        g = Graph()
        n1 = Node.allocate(10.0, 20.0)
        n2 = Node.allocate(15.0, 25.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(n1, n2)

        json_str = pu.to_json(g)
        data = json.loads(json_str)

        assert "nodes" in data
        assert "edges" in data
        assert "metadata" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_to_json_node_data(self):
        """Test that JSON export includes correct node data."""
        import json

        from hola_graph import utils as pu

        g = Graph()
        n = Node.allocate(100.0, 200.0, 30.0, 40.0)  # x, y, w, h
        g.add_node(n)

        json_str = pu.to_json(g)
        data = json.loads(json_str)

        node_data = data["nodes"][0]
        assert node_data["width"] == 30.0
        assert node_data["height"] == 40.0
        assert "x" in node_data
        assert "y" in node_data

    def test_from_json_basic(self):
        """Test basic JSON import."""
        from hola_graph import utils as pu

        json_str = """{
            "nodes": [
                {"id": 0, "x": 10, "y": 20, "width": 30, "height": 40},
                {"id": 1, "x": 50, "y": 60, "width": 30, "height": 40}
            ],
            "edges": [
                {"source": 0, "target": 1}
            ]
        }"""

        g = pu.from_json(json_str)
        assert g.get_num_nodes() == 2
        assert g.get_num_edges() == 1

    def test_from_json_positions(self):
        """Test that JSON import sets positions correctly."""
        from hola_graph import utils as pu

        json_str = """{
            "nodes": [
                {"id": 0, "x": 100.0, "y": 200.0, "width": 30, "height": 40}
            ],
            "edges": []
        }"""

        g = pu.from_json(json_str, apply_positions=True)
        nodes = g.get_nodes()
        assert len(nodes) == 1
        centre = nodes[0].get_centre()
        assert centre.x == 100.0
        assert centre.y == 200.0

    def test_json_roundtrip(self):
        """Test JSON export/import roundtrip."""
        from hola_graph import utils as pu

        # Create original graph
        g1 = Graph()
        n1 = Node.allocate(0.0, 0.0, 10.0, 20.0)
        n2 = Node.allocate(100.0, 100.0, 15.0, 25.0)
        g1.add_node(n1)
        g1.add_node(n2)
        g1.add_edge(n1, n2)

        # Export and re-import
        json_str = pu.to_json(g1)
        g2 = pu.from_json(json_str)

        assert g2.get_num_nodes() == g1.get_num_nodes()
        assert g2.get_num_edges() == g1.get_num_edges()

    def test_save_and_load_json(self):
        """Test save_json and load_json functions."""
        import tempfile

        from hola_graph import utils as pu

        g1 = Graph()
        n1 = Node.allocate(10.0, 20.0)
        n2 = Node.allocate(15.0, 25.0)
        g1.add_node(n1)
        g1.add_node(n2)
        g1.add_edge(n1, n2)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            pu.save_json(g1, temp_path)
            g2 = pu.load_json(temp_path)
            assert g2.get_num_nodes() == 2
            assert g2.get_num_edges() == 1
        finally:
            os.unlink(temp_path)

    def test_from_json_missing_nodes_field(self):
        """Test from_json with invalid JSON data."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError):
            pu.from_json('{"edges": []}')


# =============================================================================
# Input Validation Tests
# =============================================================================


class TestInputValidation:
    """Tests for input validation functions."""

    def test_validate_dimensions_positive(self):
        """Test validate_dimensions accepts positive values."""
        from hola_graph import utils as pu

        # Should not raise
        pu.validate_dimensions(10.0, 20.0)
        pu.validate_dimensions(0.001, 0.001)
        pu.validate_dimensions(1000.0, 1000.0)

    def test_validate_dimensions_zero_width(self):
        """Test validate_dimensions rejects zero width."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="width must be positive"):
            pu.validate_dimensions(0.0, 10.0)

    def test_validate_dimensions_zero_height(self):
        """Test validate_dimensions rejects zero height."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="height must be positive"):
            pu.validate_dimensions(10.0, 0.0)

    def test_validate_dimensions_negative_width(self):
        """Test validate_dimensions rejects negative width."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="width must be positive"):
            pu.validate_dimensions(-5.0, 10.0)

    def test_validate_dimensions_negative_height(self):
        """Test validate_dimensions rejects negative height."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="height must be positive"):
            pu.validate_dimensions(10.0, -5.0)

    def test_validate_dimensions_with_context(self):
        """Test validate_dimensions includes context in error."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="my_context"):
            pu.validate_dimensions(-5.0, 10.0, context="my_context")

    def test_validate_path_exists(self):
        """Test validate_path with existing file."""
        from hola_graph import utils as pu

        path = pu.validate_path(os.path.join(PARENT_DIR, "test_graph.tglf"))
        assert path.exists()

    def test_validate_path_not_found(self):
        """Test validate_path with non-existent file."""
        from hola_graph import utils as pu

        with pytest.raises(FileNotFoundError, match="File not found"):
            pu.validate_path("/nonexistent/path.txt")

    def test_validate_path_wrong_suffix(self):
        """Test validate_path with wrong file extension."""
        import tempfile

        from hola_graph import utils as pu

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match=r"Expected \.json file"):
                pu.validate_path(temp_path, expected_suffix=".json")
        finally:
            os.unlink(temp_path)

    def test_validate_path_no_existence_check(self):
        """Test validate_path with must_exist=False."""
        from hola_graph import utils as pu

        # Should not raise even though file doesn't exist
        path = pu.validate_path("/nonexistent/path.txt", must_exist=False)
        assert str(path) == "/nonexistent/path.txt"

    def test_create_node_valid(self):
        """Test create_node with valid dimensions."""
        from hola_graph import utils as pu

        node = pu.create_node(10.0, 20.0)
        dims = node.get_dimensions()
        assert dims == (10.0, 20.0)

    def test_create_node_with_position(self):
        """Test create_node with position."""
        from hola_graph import utils as pu

        node = pu.create_node(10.0, 20.0, x=50.0, y=100.0)
        dims = node.get_dimensions()
        centre = node.get_centre()
        assert dims == (10.0, 20.0)
        assert centre.x == 50.0
        assert centre.y == 100.0

    def test_create_node_invalid_width(self):
        """Test create_node rejects invalid width."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="width must be positive"):
            pu.create_node(0.0, 10.0)

    def test_create_node_invalid_height(self):
        """Test create_node rejects invalid height."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="height must be positive"):
            pu.create_node(10.0, -5.0)

    def test_graph_builder_validates_dimensions(self):
        """Test GraphBuilder validates node dimensions."""
        from hola_graph import utils as pu

        builder = pu.GraphBuilder()
        with pytest.raises(ValueError, match="width must be positive"):
            builder.add_node(0.0, 10.0, name="A")

    def test_create_graph_validates_dimensions(self):
        """Test create_graph validates node dimensions."""
        from hola_graph import utils as pu

        with pytest.raises(ValueError, match="width must be positive"):
            pu.create_graph(((0.0, 10.0), (20.0, 20.0)))

    def test_from_json_validates_dimensions(self):
        """Test from_json validates node dimensions."""
        from hola_graph import utils as pu

        json_str = """{
            "nodes": [
                {"id": 0, "x": 10, "y": 20, "width": 0, "height": 40}
            ],
            "edges": []
        }"""

        with pytest.raises(ValueError, match="width must be positive"):
            pu.from_json(json_str)

    def test_load_json_validates_extension(self):
        """Test load_json validates file extension."""
        import tempfile

        from hola_graph import utils as pu

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b'{"nodes": [], "edges": []}')
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match=r"Expected \.json file"):
                pu.load_json(temp_path)
        finally:
            os.unlink(temp_path)


# =============================================================================
# Matplotlib Visualization Tests
# =============================================================================


class TestMatplotlibVisualization:
    """Tests for Matplotlib visualization functionality."""

    def test_plot_graph_import(self):
        """Test that plot_graph can be imported."""
        from hola_graph import utils as pu

        assert hasattr(pu, "plot_graph")
        assert hasattr(pu, "save_plot")
        assert hasattr(pu, "plot_comparison")

    def test_plot_graph_basic(self):
        """Test basic plot_graph functionality."""
        pytest.importorskip("matplotlib")
        import matplotlib

        from hola_graph import utils as pu

        matplotlib.use("Agg")  # Use non-interactive backend

        g = get_test_graph()
        do_hola(g)

        ax = pu.plot_graph(g, title="Test Graph")
        assert ax is not None

    def test_plot_graph_empty(self):
        """Test plot_graph with empty graph."""
        pytest.importorskip("matplotlib")
        import matplotlib

        from hola_graph import utils as pu

        matplotlib.use("Agg")

        g = Graph()
        ax = pu.plot_graph(g, title="Empty Graph")
        assert ax is not None

    def test_plot_graph_custom_options(self):
        """Test plot_graph with custom styling options."""
        pytest.importorskip("matplotlib")
        import matplotlib

        from hola_graph import utils as pu

        matplotlib.use("Agg")

        g = Graph()
        n1 = Node.allocate(0.0, 0.0, 20.0, 20.0)
        n2 = Node.allocate(50.0, 50.0, 20.0, 20.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(n1, n2)

        ax = pu.plot_graph(
            g,
            show_node_ids=False,
            node_color="red",
            edge_color="blue",
            node_alpha=0.5,
            edge_alpha=0.3,
        )
        assert ax is not None

    def test_save_plot(self):
        """Test save_plot function."""
        pytest.importorskip("matplotlib")
        import matplotlib

        from hola_graph import utils as pu

        matplotlib.use("Agg")
        import tempfile

        g = Graph()
        n1 = Node.allocate(0.0, 0.0, 20.0, 20.0)
        n2 = Node.allocate(50.0, 50.0, 20.0, 20.0)
        g.add_node(n1)
        g.add_node(n2)
        g.add_edge(n1, n2)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            pu.save_plot(g, temp_path, title="Test Save")
            assert os.path.exists(temp_path)
            # Check file has content
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_plot_comparison(self):
        """Test plot_comparison function."""
        pytest.importorskip("matplotlib")
        import matplotlib

        from hola_graph import utils as pu

        matplotlib.use("Agg")

        g1 = Graph()
        n1 = Node.allocate(0.0, 0.0, 20.0, 20.0)
        n2 = Node.allocate(50.0, 0.0, 20.0, 20.0)
        g1.add_node(n1)
        g1.add_node(n2)
        g1.add_edge(n1, n2)

        g2 = Graph()
        n3 = Node.allocate(0.0, 0.0, 20.0, 20.0)
        n4 = Node.allocate(0.0, 50.0, 20.0, 20.0)
        g2.add_node(n3)
        g2.add_node(n4)
        g2.add_edge(n3, n4)

        fig, (ax1, ax2) = pu.plot_comparison(g1, g2, titles=("Graph 1", "Graph 2"))
        assert fig is not None
        assert ax1 is not None
        assert ax2 is not None
