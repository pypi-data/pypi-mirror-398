# TODO

## High Priority

- [ ] Incremental layout support (LayoutSession class for interactive editing)

## Completed

- [x] Add CI/CD pipeline (GitHub Actions for build/test on multiple platforms)
- [x] Add `__iter__` for Graph (yield nodes/edges for Pythonic iteration)
- [x] Create Python wrapper layer (`src/hola_graph/api.py` with enhanced API)
- [x] Layout algorithm options presets (compact, readable, etc.)
- [x] Fix mixed build outputs (`.so` files in `src/` should go to `build/`)
- [x] Fix typos in _core.cpp
- [x] Fix empty docstrings in _core.cpp (HolaOpts, OrderedAlignment, ACAFlag, ACASepFlag)
- [x] Fix avoid submodule description
- [x] Replace deprecated `<string.h>` with `<cstring>` in _core.cpp
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
