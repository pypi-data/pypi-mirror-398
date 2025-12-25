# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.5]

### Added

- Makefile targets for PyPI publishing: `check-dist`, `publish`, `publish-test`

### Changed

- Consolidated CI workflows: removed `wheels.yml`, using `build-wheels.yml` for all wheel builds
- Simplified macOS wheel builds to arm64 only (x86_64 dropped due to cross-compilation issues)

### Fixed

- Added missing docstrings for `HolaOpts`, `OrderedAlignment`, `ACAFlag`, `ACASepFlag` in C++ bindings

## [0.1.4]

### Added

- New high-level Pythonic API with `HolaGraph`, `HolaNode`, and `HolaEdge` classes
  - `HolaGraph`: wrapper with `add_node()`, `connect()`, `layout()`, `to_svg()` methods
  - `HolaNode`: node wrapper with `position`, `size`, `x`, `y`, `width`, `height`, `label` properties
  - `HolaEdge`: frozen dataclass with `source`, `target`, `id` attributes
  - Optional node labels with auto-generation (A, B, C, ... Z, AA, AB, ...)
  - Load from TGLF files with `HolaGraph.from_tglf()`
  - Iterate over nodes and edges with `graph.nodes` and `graph.edges` properties

### Changed

- **BREAKING**: Renamed project from `pyhola` to `hola-graph`
  - PyPI package: `hola-graph` (install with `pip install hola-graph`)
  - Python import: `hola_graph` (use `import hola_graph`)
  - All internal references updated to new naming
- **BREAKING**: Default exports changed to new high-level API only
  - `from hola_graph import HolaGraph, HolaNode, HolaEdge` (new default)
  - Low-level C++ bindings moved to `hola_graph._core` module
  - Use `from hola_graph._core import Graph, Node, Edge, do_hola` for direct C++ access
  - Utilities remain at `from hola_graph import utils`

### Fixed

- Fixed Linux build: disabled LTO to prevent "plugin needed to handle lto object" linker error
- Fixed Linux linking: use `--start-group`/`--end-group` for static library circular dependencies
- Fixed `avoid.Point()` default constructor to initialize x,y to 0.0 (was uninitialized)
- Fixed CI wheel tests: override pythonpath to test installed wheel instead of source directory

## [0.1.3]

### Changed

- **BREAKING**: Migrated build system from setuptools to scikit-build-core
  - Removed `setup.py` and `MANIFEST.in`
  - CMake is now the sole build system
  - Requires Python 3.9+ (was 3.7+)

## [0.1.2]

### Added

- `tests/test_examples.py` with matplotlib and NetworkX visualization examples
  - Generates example outputs to `build/test-outputs/` during test runs
  - Includes before/after layout comparisons, NetworkX integration demos
- New Graph methods:
  - `__iter__`: iterate over nodes with `for node in graph:`
  - `__str__`: user-friendly string representation
  - `add_nodes(nodes)`: bulk add multiple nodes
  - `clear()`: remove all nodes and edges
- `__str__` methods for Node and Edge classes

### Changed

- **BREAKING**: Restructured as proper Python package `pyhola`:
  - C++ extension now at `pyhola._core` (was top-level `pyhola` module)
  - Utilities now at `pyhola.utils` (was `pyhola_utils`)
  - All public APIs re-exported from `pyhola` package for convenience
  - Import `from pyhola import Graph, Node, do_hola, GraphBuilder` works as before
- Rewrote `README.md` with comprehensive documentation
- License changed from public domain to MIT

### Fixed

- Return value policies for raw pointer returns now use `reference_internal` to prevent dangling pointers

## [0.1.1]

### Added

- Type stubs (`pyhola.pyi`) for IDE autocompletion and type checking
- `pyhola_utils` module with enhanced Python API:
  - `load_graph()`, `save_svg()`, `save_tglf()` for file operations
  - `GraphBuilder` class for fluent graph construction
  - `layout_context()` context manager for temporary layout changes
  - `graph_stats()` and `print_graph_info()` for graph analysis
  - `compact_layout_opts()` and `spacious_layout_opts()` presets
  - NetworkX interoperability: `to_networkx()`, `from_networkx()`, `layout_networkx()`
  - JSON import/export: `to_json()`, `from_json()`, `save_json()`, `load_json()`
  - Matplotlib visualization: `plot_graph()`, `save_plot()`, `plot_comparison()`
- Pythonic Graph API:
  - `len(graph)` returns number of nodes
  - `node_id in graph` membership testing
  - `graph.get_nodes()` returns list of nodes
- `pyhola.version_info` tuple for programmatic version access
- `__repr__` methods for Graph, Node, and Edge classes
- CI/CD pipeline with GitHub Actions
- Comprehensive test suite (89 tests)
- CONTRIBUTING.md with development guidelines

### Changed

- macOS deployment target now auto-detected instead of hardcoded
- Improved docstrings throughout C++ bindings
- Updated Makefile with `lint`, `format`, and `rebuild` targets

### Fixed

- Typo "ndoes" corrected to "nodes" in `pad_all_nodes` docstring
- Empty docstrings for rotation and projection methods
- Incorrect `avoid` submodule description

## [0.1.0]

### Added

- Initial release
- Python bindings for HOLA layout algorithm via pybind11
- Core classes: `Graph`, `Node`, `Edge`
- Layout options: `HolaOpts`, `ColaOptions`
- TGLF file format support
- SVG export
- `avoid` submodule with geometric types (`Point`, `Box`, `Polygon`, `Rectangle`)
- Automatic adaptagrams dependency download and build
- CMake and setup.py build systems
