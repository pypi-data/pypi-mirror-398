"""Generate example outputs for matplotlib and NetworkX visualization."""

import os

import pytest

PARENT_DIR = os.path.dirname(__file__)
BUILD_DIR = os.path.join(os.path.dirname(PARENT_DIR), "build")
OUTPUTS_DIR = os.path.join(BUILD_DIR, "test-outputs")


def ensure_outputs_dir():
    """Create outputs directory if it doesn't exist."""
    os.makedirs(OUTPUTS_DIR, exist_ok=True)


class TestMatplotlibExamples:
    """Generate matplotlib visualization examples."""

    def test_basic_graph_plot(self):
        """Generate a basic graph visualization."""
        pytest.importorskip("matplotlib")
        import matplotlib

        matplotlib.use("Agg")

        from hola_graph import utils as pu
        from hola_graph._core import Graph, Node, do_hola

        ensure_outputs_dir()

        # Create a simple graph
        g = Graph()
        nodes = [Node.allocate(30, 20) for _ in range(5)]
        for n in nodes:
            g.add_node(n)

        # Create edges: 0-1, 1-2, 2-3, 3-4, 4-0 (cycle)
        for i in range(5):
            g.add_edge(nodes[i], nodes[(i + 1) % 5])

        # Apply layout
        do_hola(g)

        # Save visualization
        output_path = os.path.join(OUTPUTS_DIR, "basic_graph.png")
        pu.save_plot(g, output_path, title="Basic Graph (5-node cycle)", dpi=150)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_before_after_layout(self):
        """Generate before/after layout comparison."""
        pytest.importorskip("matplotlib")
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from hola_graph import utils as pu
        from hola_graph._core import Graph, Node, do_hola

        ensure_outputs_dir()

        # Create a tree-like graph
        g = Graph()
        root = Node.allocate(0, 0, 40, 25)
        g.add_node(root)

        children = []
        for i in range(3):
            child = Node.allocate(i * 60, 80, 35, 20)
            g.add_node(child)
            g.add_edge(root, child)
            children.append(child)

        grandchildren = []
        for i, parent in enumerate(children):
            for j in range(2):
                gc = Node.allocate(i * 60 + j * 30, 160, 30, 18)
                g.add_node(gc)
                g.add_edge(parent, gc)
                grandchildren.append(gc)

        # Save before layout
        before_path = os.path.join(OUTPUTS_DIR, "tree_before_layout.png")
        pu.save_plot(g, before_path, title="Tree Graph - Before HOLA", dpi=150)

        # Apply HOLA layout
        do_hola(g)

        # Save after layout
        after_path = os.path.join(OUTPUTS_DIR, "tree_after_layout.png")
        pu.save_plot(g, after_path, title="Tree Graph - After HOLA", dpi=150)

        # Also save a side-by-side comparison
        # Note: We need to recreate the before state for comparison
        g_before = Graph()
        root_b = Node.allocate(0, 0, 40, 25)
        g_before.add_node(root_b)
        children_b = []
        for i in range(3):
            child = Node.allocate(i * 60, 80, 35, 20)
            g_before.add_node(child)
            g_before.add_edge(root_b, child)
            children_b.append(child)
        for i, parent in enumerate(children_b):
            for j in range(2):
                gc = Node.allocate(i * 60 + j * 30, 160, 30, 18)
                g_before.add_node(gc)
                g_before.add_edge(parent, gc)

        fig, (_ax1, _ax2) = pu.plot_comparison(
            g_before, g, titles=("Before HOLA", "After HOLA"), figsize=(14, 6)
        )
        comparison_path = os.path.join(OUTPUTS_DIR, "tree_comparison.png")
        fig.savefig(comparison_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        assert os.path.exists(before_path)
        assert os.path.exists(after_path)
        assert os.path.exists(comparison_path)

    def test_graph_builder_plot(self):
        """Generate visualization using GraphBuilder."""
        pytest.importorskip("matplotlib")
        import matplotlib

        matplotlib.use("Agg")

        from hola_graph import utils as pu

        ensure_outputs_dir()

        # Use GraphBuilder to create a graph
        g = (
            pu.GraphBuilder()
            .add_node(40, 25, name="A")
            .add_node(40, 25, name="B")
            .add_node(40, 25, name="C")
            .add_node(40, 25, name="D")
            .add_node(40, 25, name="E")
            .add_edge("A", "B")
            .add_edge("A", "C")
            .add_edge("B", "D")
            .add_edge("C", "D")
            .add_edge("D", "E")
            .layout()
            .build()
        )

        output_path = os.path.join(OUTPUTS_DIR, "graph_builder_example.png")
        pu.save_plot(
            g,
            output_path,
            title="Graph Built with GraphBuilder",
            node_color="lightgreen",
            dpi=150,
        )

        assert os.path.exists(output_path)


class TestNetworkXExamples:
    """Generate NetworkX integration examples."""

    def test_networkx_to_hola_graph(self):
        """Convert NetworkX graph to hola_graph and visualize."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("networkx")
        import matplotlib

        matplotlib.use("Agg")
        import networkx as nx

        from hola_graph import utils as pu
        from hola_graph._core import do_hola

        ensure_outputs_dir()

        # Create a NetworkX graph (Petersen graph - a classic example)
        nx_graph = nx.petersen_graph()

        # Convert to hola_graph
        g = pu.from_networkx(nx_graph, node_width=25, node_height=25)

        # Apply HOLA layout
        do_hola(g)

        # Save hola_graph visualization
        output_path = os.path.join(OUTPUTS_DIR, "networkx_petersen_hola_graph.png")
        pu.save_plot(
            g,
            output_path,
            title="Petersen Graph (NetworkX -> hola_graph -> HOLA)",
            node_color="lightyellow",
            dpi=150,
        )

        assert os.path.exists(output_path)

    def test_networkx_layout_positions(self):
        """Use HOLA positions in NetworkX visualization."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("networkx")
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx

        from hola_graph import utils as pu

        ensure_outputs_dir()

        # Create a NetworkX graph
        nx_graph = nx.karate_club_graph()

        # Get HOLA layout positions
        pos = pu.layout_networkx(nx_graph, node_width=20, node_height=20)

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Draw with spring layout (default)
        ax1.set_title("Karate Club - Spring Layout")
        spring_pos = nx.spring_layout(nx_graph, seed=42)
        nx.draw(
            nx_graph,
            pos=spring_pos,
            ax=ax1,
            node_color="lightblue",
            node_size=300,
            with_labels=True,
            font_size=8,
        )

        # Draw with HOLA layout
        ax2.set_title("Karate Club - HOLA Layout")
        nx.draw(
            nx_graph,
            pos=pos,
            ax=ax2,
            node_color="lightgreen",
            node_size=300,
            with_labels=True,
            font_size=8,
        )

        output_path = os.path.join(OUTPUTS_DIR, "networkx_karate_comparison.png")
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        assert os.path.exists(output_path)

    def test_hola_graph_to_networkx(self):
        """Convert hola_graph graph to NetworkX and visualize both."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("networkx")
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx

        from hola_graph import utils as pu

        ensure_outputs_dir()

        # Create a hola_graph graph using GraphBuilder
        g = (
            pu.GraphBuilder()
            .add_node(30, 20, name="A")
            .add_node(30, 20, name="B")
            .add_node(30, 20, name="C")
            .add_node(30, 20, name="D")
            .add_node(30, 20, name="E")
            .add_node(30, 20, name="F")
            .add_edge("A", "B")
            .add_edge("A", "C")
            .add_edge("B", "D")
            .add_edge("C", "D")
            .add_edge("C", "E")
            .add_edge("D", "F")
            .add_edge("E", "F")
            .layout()
            .build()
        )

        # Convert to NetworkX
        nx_graph = pu.to_networkx(g, include_positions=True)

        # Get positions from the converted graph
        pos = nx.get_node_attributes(nx_graph, "pos")

        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # Draw hola_graph visualization
        ax1.set_title("hola_graph Visualization")
        pu.plot_graph(g, ax=ax1, node_color="lightcoral")

        # Draw NetworkX visualization using same positions
        ax2.set_title("NetworkX Visualization (same positions)")
        nx.draw(
            nx_graph,
            pos=pos,
            ax=ax2,
            node_color="lightcoral",
            node_size=500,
            with_labels=True,
            font_size=10,
            font_weight="bold",
        )

        output_path = os.path.join(OUTPUTS_DIR, "hola_graph_to_networkx.png")
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        assert os.path.exists(output_path)

    def test_networkx_graph_types(self):
        """Generate examples with different NetworkX graph types."""
        pytest.importorskip("matplotlib")
        pytest.importorskip("networkx")
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import networkx as nx

        from hola_graph import utils as pu

        ensure_outputs_dir()

        # Create different graph types
        graphs = {
            "Complete (K5)": nx.complete_graph(5),
            "Cycle (C8)": nx.cycle_graph(8),
            "Star (S6)": nx.star_graph(6),
            "Binary Tree": nx.balanced_tree(2, 3),
        }

        fig, axes = plt.subplots(2, 2, figsize=(12, 12))
        axes = axes.flatten()

        for ax, (name, nx_graph) in zip(axes, graphs.items()):
            # Get HOLA layout
            pos = pu.layout_networkx(nx_graph, node_width=25, node_height=25)

            ax.set_title(f"{name} - HOLA Layout")
            nx.draw(
                nx_graph,
                pos=pos,
                ax=ax,
                node_color="lightskyblue",
                node_size=400,
                with_labels=True,
                font_size=9,
                font_weight="bold",
                edge_color="gray",
            )

        output_path = os.path.join(OUTPUTS_DIR, "networkx_graph_types.png")
        fig.tight_layout()
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        assert os.path.exists(output_path)
