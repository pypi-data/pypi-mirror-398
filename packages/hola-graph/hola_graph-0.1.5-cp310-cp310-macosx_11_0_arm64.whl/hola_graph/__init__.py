"""hola_graph: Python bindings for HOLA (Human-like Orthogonal Layout Algorithm).

This package provides Python bindings for the HOLA algorithm from the
adaptagrams C++ library.

Example:
    >>> from hola_graph import HolaGraph
    >>> g = HolaGraph()
    >>> a = g.add_node(30, 20, label="A")
    >>> b = g.add_node(30, 20, label="B")
    >>> g.connect(a, b)
    >>> g.layout()
    >>> g.to_svg("output.svg")

For low-level C++ bindings, use:
    >>> from hola_graph import _core
    >>> from hola_graph._core import Graph, Node, do_hola

For utility functions, use:
    >>> from hola_graph import utils
    >>> from hola_graph.utils import plot_graph, to_networkx
"""

from hola_graph.api import HolaEdge, HolaGraph, HolaNode

__all__ = [
    "HolaEdge",
    "HolaGraph",
    "HolaNode",
]
