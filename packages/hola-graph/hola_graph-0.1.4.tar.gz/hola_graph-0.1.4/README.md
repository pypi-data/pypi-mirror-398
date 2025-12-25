# hola-graph

A Python wrapper for the HOLA (Human-like Orthogonal Layout Algorithm) from the [adaptagrams](https://github.com/mjwybrow/adaptagrams) C++ library. HOLA produces graph layouts that approximate what a human would create - clean, orthogonal, and aesthetically pleasing.

Based on the research paper: [HOLA: Human-like Orthogonal Network Layout](https://skieffer.info/publications/kieffer2016hola.pdf) (Kieffer, Dwyer, Marriott, Wybrow - IEEE TVCG 2016).

## Features

- **HOLA Layout Algorithm**: Produces human-like orthogonal graph layouts
- **High-Level API**: `HolaGraph`, `HolaNode`, `HolaEdge` classes with Pythonic interface
- **Low-Level Bindings**: Direct access to C++ classes via `hola_graph._core`
- **File I/O**: Load/save graphs in TGLF format, export to SVG and JSON
- **NetworkX Integration**: Convert between hola-graph and NetworkX graphs
- **Matplotlib Visualization**: Plot graphs directly with customizable styling
- **Layout Options**: Configurable via HolaOpts and ColaOptions classes
- **Geometric Types**: Point, Box, Polygon, Rectangle from libavoid

## Installation

### Requirements

- Python 3.9+
- C++14 compatible compiler
- CMake 3.18+

### Building

```bash
# Clone the repository
git clone https://github.com/shakfu/hola-graph.git
cd hola-graph

# Build (downloads and compiles adaptagrams automatically)
make
# or
make build

# Run tests to verify installation
make test
```

Or build directly with uv/pip:

```bash
uv build   # Creates wheel and sdist in dist/
pip install .
```

## Quick Start

### Basic Usage (High-Level API)

```python
from hola_graph import HolaGraph

# Create a graph
g = HolaGraph()

# Add nodes (width, height) - returns the created node
a = g.add_node(30, 20, label="A")
b = g.add_node(30, 20, label="B")
c = g.add_node(30, 20, label="C")

# Connect nodes
g.connect(a, b)
g.connect(b, c)

# Apply HOLA layout
g.layout()

# Export to SVG
g.to_svg("graph.svg")

# Access node properties
print(f"Node A position: ({a.x}, {a.y})")
print(f"Node A size: {a.width} x {a.height}")
```

### Loading from File

```python
from hola_graph import HolaGraph

# Load, layout, and export
g = HolaGraph.from_tglf("input.tglf")
g.layout()
g.to_svg("output.svg")

# Iterate over nodes and edges
for node in g.nodes:
    print(f"{node.label}: ({node.x}, {node.y})")

for edge in g.edges:
    print(f"Edge {edge.id}: {edge.source} -> {edge.target}")
```

### Low-Level API (Direct C++ Bindings)

For advanced use cases, access the C++ bindings directly:

```python
from hola_graph._core import Graph, Node, Edge, do_hola, HolaOpts

# Create a graph
g = Graph()

# Add nodes (width, height)
n1 = Node.allocate(30, 20)
n2 = Node.allocate(30, 20)
g.add_node(n1)
g.add_node(n2)
g.add_edge(n1, n2)

# Apply layout with options
opts = HolaOpts()
opts.nodePaddingScalar = 1.5
do_hola(g, opts)

# Export
with open("graph.svg", "w") as f:
    f.write(g.to_svg())
```

### NetworkX Integration

```python
import networkx as nx
from hola_graph import utils as pu

# Create from NetworkX graph
nx_graph = nx.karate_club_graph()
g = pu.from_networkx(nx_graph, node_width=25, node_height=25)
pu.apply_hola(g)

# Or get positions for NetworkX visualization
pos = pu.layout_networkx(nx_graph)
nx.draw(nx_graph, pos=pos)
```

### Matplotlib Visualization

```python
from hola_graph import utils as pu
import matplotlib.pyplot as plt

g = pu.load_graph("graph.tglf")
pu.apply_hola(g)

# Display
pu.plot_graph(g, title="My Graph", node_color="lightgreen")
plt.show()

# Or save to file
pu.save_plot(g, "graph.png", dpi=150)
```

### JSON Serialization

```python
from hola_graph import utils as pu

# Export to JSON
json_str = pu.to_json(g)
pu.save_json(g, "graph.json")

# Import from JSON
g = pu.from_json(json_str)
g = pu.load_json("graph.json")
```

## API Reference

### High-Level API (hola_graph)

| Class | Description |
|-------|-------------|
| `HolaGraph` | Main graph class with Pythonic interface |
| `HolaNode` | Node with position, size, and label properties |
| `HolaEdge` | Frozen dataclass representing an edge |

#### HolaGraph Methods

```python
# Construction
g = HolaGraph()                     # Create empty graph
g = HolaGraph.from_tglf(path)       # Load from TGLF file

# Adding nodes and edges
node = g.add_node(w, h)             # Add node, returns HolaNode
node = g.add_node(w, h, label="A")  # Add node with label
g.connect(node1, node2)             # Connect two nodes

# Layout and export
g.layout()                          # Apply HOLA layout
g.layout(opts)                      # Apply with HolaOpts
g.to_svg(path)                      # Export to SVG file
svg_str = g.to_svg()                # Get SVG as string
tglf_str = g.to_tglf()              # Get TGLF as string

# Properties
g.nodes                             # List of HolaNode objects
g.edges                             # List of HolaEdge objects
len(g)                              # Number of nodes
```

#### HolaNode Properties

```python
node.id                             # Unique node ID
node.label                          # Node label (auto-generated if not set)
node.x, node.y                      # Center position
node.position                       # (x, y) tuple
node.width, node.height             # Dimensions
node.size                           # (width, height) tuple
```

#### HolaEdge Attributes

```python
edge.id                             # Unique edge ID
edge.source                         # Source node ID
edge.target                         # Target node ID
```

### Low-Level API (hola_graph._core)

| Class | Description |
|-------|-------------|
| `Graph` | C++ graph container |
| `Node` | C++ graph vertex |
| `Edge` | C++ connection between nodes |
| `HolaOpts` | Configuration for HOLA algorithm |
| `ColaOptions` | Configuration for constraint-based layout |

| Function | Description |
|----------|-------------|
| `do_hola(graph, opts=None)` | Apply HOLA layout algorithm |
| `graph_from_tglf_file(path)` | Load graph from TGLF file |

### Utility Functions (hola_graph.utils)

```python
# File I/O
load_graph(path)                    # Load from TGLF
save_svg(graph, path)               # Save as SVG
save_tglf(graph, path)              # Save as TGLF
load_json(path) / save_json(g, p)   # JSON I/O

# Graph building
create_node(w, h, x=None, y=None)   # Create validated node
GraphBuilder()                       # Fluent graph construction

# Layout helpers
apply_hola(graph, opts=None)        # Apply layout, return graph
compact_layout_opts()               # Preset for dense layouts
spacious_layout_opts()              # Preset for spread-out layouts
layout_context(graph)               # Context manager for temporary layout

# Analysis
graph_stats(graph)                  # Get statistics dict
print_graph_info(graph)             # Print summary

# NetworkX
to_networkx(graph)                  # Convert to NetworkX
from_networkx(nx_graph)             # Convert from NetworkX
layout_networkx(nx_graph)           # Get HOLA positions for NetworkX

# Visualization
plot_graph(graph, ax=None, ...)     # Plot with matplotlib
save_plot(graph, path, ...)         # Save visualization
plot_comparison(g1, g2, ...)        # Side-by-side comparison
```

## Optional Dependencies

Install with pip for additional features:

```bash
pip install networkx    # For NetworkX integration
pip install matplotlib  # For visualization
```

Or install all optional dependencies:

```bash
pip install hola-graph[all]
```

## SWIG Wrapper

The adaptagrams library also provides a comprehensive SWIG-based Python wrapper. If `swig` is available, build it with:

```bash
make swig-python
```

The extension will be in `build/adaptagrams/build`.

## Credits

HOLA algorithm authors:
> Steve Kieffer, Tim Dwyer, Kim Marriott, and Michael Wybrow.
> HOLA: Human-like Orthogonal Network Layout.
> IEEE Transactions on Visualization and Computer Graphics, Volume 22, Issue 1, pages 349-358. IEEE, 2016.

This project builds against a [fork of adaptagrams](https://github.com/shakfu/adaptagrams) with CMake support.

Thanks to [Wenzel Jakob](https://github.com/wjakob) for pybind11.

## License

MIT License. See [LICENSE](LICENSE) for details.
