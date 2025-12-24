# Repository Layout
- `src/covers/` - Python source code (main interface, imports from Rust core)
- `src_rust/` - Rust implementation core (performance-critical code coverage logic)
- `tests/` - Test suite including unit tests and integration tests
- `benchmarks/` - Performance benchmarks and comparison tools
- `tools/` - Utility scripts for development and analysis
- `docs/` - Documentation and assets
- `.github/` - CI/CD workflows and GitHub configuration

# Workflow
- Run `mise run build` to build the project.
- Run `mise run lint` to run linters after every edit.
- Run `mise run test` to run the entire test suite.
- Run `mise run test tests/test_coverage.py` to run a specific test file
- Run `mise run test_all_versions` to run tests against all suported versions of Python. Only run this when explicitly dealing with differences in behavior between Python versions.

# Code Style Guidelines
- Python: Use ruff for formatting and linting (configured in pyproject.toml)
- Rust: Use rustfmt and clippy (configured via mise run lint)
- Imports: Python uses `from __future__ import annotations`, Rust imports are organized alphabetically
- Error handling: Python uses proper exception handling, Rust uses Result<> types
- Types: Python uses TYPE_CHECKING for forward references, Rust uses strong typing
- Naming: Python follows PEP 8, Rust follows snake_case for functions, PascalCase for types

# Python to Rust Conversion Guidelines
When converting Python code to Rust, follow these guidelines:
- Always remove the original Python implementations after converting to Rust; do not keep a fallback Python implementation.
- Never call Python code from Rust; when converting a function, always convert all functions that are called from it.
- Avoid using PyDict / PyList and similar; prefer to use pure-Rust equivalents. Use ahash in place of dicts, tree-sitter in place of ast, and similar.
- When adding a crate, always verify that you are using the latest available version.