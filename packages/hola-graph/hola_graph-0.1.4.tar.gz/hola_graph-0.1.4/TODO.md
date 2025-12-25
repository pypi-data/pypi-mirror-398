# TODO

## High Priority

- [x] Add CI/CD pipeline (GitHub Actions for build/test on multiple platforms)

## Medium Priority

- [x] Add `__iter__` for Graph (yield nodes/edges for Pythonic iteration)
- [ ] Fix mixed build outputs (`.so` files in `src/` should go to `build/`)
- [x] Create Python wrapper layer (`src/hola_graph/api.py` with enhanced API)
- [ ] Layout algorithm options presets (compact, readable, etc.)

## Low Priority

- [ ] Fix typos in hola_graph.cpp (line 111: "ndoes" -> "nodes")
- [ ] Fix empty docstrings in hola_graph.cpp (lines 85-87, 100-101)
- [ ] Fix avoid submodule description (line 808: "example" -> proper description)
- [ ] Replace deprecated `<string.h>` with `<cstring>` in hola_graph.cpp
- [ ] Incremental layout support (LayoutSession class)

## Completed

- [x] Type stubs (.pyi file)
- [x] `__repr__` methods for Graph, Node, Edge
- [x] `__len__` and `__contains__` for Graph
- [x] `version_info` tuple
- [x] CHANGELOG.md
- [x] CONTRIBUTING.md
- [x] Dead code cleanup (removed tests/test_node/)
- [x] NetworkX interoperability
- [x] JSON import/export
- [x] Matplotlib integration
- [x] Build system improvements (Makefile, setup.sh, CMake, pyproject.toml)
- [x] Expanded test coverage (89 tests)
- [x] Lint clean (ruff)
- [x] Type check clean (mypy)
- [x] Input validation (file paths, dimensions > 0)
