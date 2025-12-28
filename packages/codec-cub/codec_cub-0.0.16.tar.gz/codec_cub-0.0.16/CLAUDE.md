# CLAUDE.md

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

## Project Overview

**codec-cub** is a comprehensive Python library for encoding, decoding, and manipulating various file formats and data structures. It provides specialized codecs and file handlers for:

- **Python Code Generation**: Fluent builders for generating Python code (classes, functions, imports, docstrings, type annotations)
- **Configuration Formats**: TOML, YAML, JSON/JSONL
- **Serialization**: MessagePack with custom extension types
- **Custom Formats**: TOON (indentation-based format), NIX expressions
- **Text/XML Processing**: File handlers with locking and atomic operations
- **General Utilities**: Base file handlers, mock text generation, file info/locking

The library emphasizes type safety (strict Pyright checking), builder patterns for fluent APIs, and proper resource management.

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

## Development Commands

### Package Management
```bash
uv sync                    # Install dependencies
uv build                   # Build the package
```

### CLI Testing
```bash
codec-cub --help          # Show available commands
codec-cub version         # Get current version
codec-cub bump patch      # Bump version (patch/minor/major)
codec-cub debug_info      # Show environment info
```


### Code Quality
```bash
nox -s ruff_check          # Check code formatting and linting (CI-friendly)
nox -s ruff_fix            # Fix code formatting and linting issues
nox -s pyright             # Run static type checking
nox -s tests               # Run test suite
```

### Version Management
```bash
git tag v1.0.0             # Manual version tagging
codec-cub bump patch      # Automated version bump with git tag
```

## Architecture

### Core Components

- **CLI Module** (`src/codec_cub/_internal/cli.py`): Main CLI interface using Typer with dependency injection
- **Dependency Injection** (`src/codec_cub/_internal/_di.py`): Uses `dependency-injector` for IoC container
- **Debug/Info** (`src/codec_cub/_internal/debug.py`): Environment and package information utilities
- **Version Management** (`src/codec_cub/_internal/_version.py`): Dynamic versioning from git tags
- **Configuration** (`src/codec_cub/config.py`): Application configuration with Pydantic

### Key Dependencies

- **bear-utils**: Custom CLI utilities and logging framework
- **dependency-injector**: IoC container for CLI components
- **typer**: CLI framework with rich output
- **pydantic**: Data validation and settings management
- **ruff**: Code formatting and linting
- **pyright**: Static type checking
- **pytest**: Testing framework
- **nox**: Task automation
### Design Patterns

1. **Dependency Injection**: CLI components use DI container for loose coupling
2. **Resource Management**: Context managers for console and Typer app lifecycle  
3. **Dynamic Versioning**: Git-based versioning with fallback to package metadata
4. **Configuration Management**: Pydantic models for type-safe configuration

## Project Structure

```
codec-cub/
├── src/codec_cub/
│   ├── _internal/                    # Internal CLI and version management
│   │   ├── cli.py                    # Typer-based CLI with dependency injection
│   │   ├── debug.py                  # Environment and package info utilities
│   │   ├── _version.py               # Git-based dynamic versioning
│   │   └── _versioning.py            # Version helpers
│   ├── pythons/                      # Python code generation framework
│   │   ├── builders/                 # Fluent builder pattern implementations
│   │   │   ├── class_builder.py      # Class definitions with methods/properties
│   │   │   ├── docstring_builder.py  # Google/NumPy style docstrings
│   │   │   ├── enum_builder.py       # Enum class generation
│   │   │   ├── fluent_builders.py    # Literal/TypedDict builders
│   │   │   ├── function_builder.py   # Function/method definitions
│   │   │   └── import_builder.py     # Import statement manager with deduplication
│   │   ├── codec.py                  # Python AST codec
│   │   ├── file_builder.py           # Complete Python file generation
│   │   ├── python_writer.py          # Low-level Python code writer
│   │   ├── type_annotation.py        # Type annotation builder
│   │   └── helpers.py                # Naming conventions, formatters
│   ├── message_pack/                 # MessagePack encoding/decoding
│   │   ├── packing.py                # Custom type serialization
│   │   ├── unpacking.py              # Custom type deserialization
│   │   ├── file_handler.py           # MessagePack file I/O
│   │   └── common/                   # Extension type definitions
│   ├── toon/                         # TOON format (indentation-based serialization)
│   │   ├── codec.py                  # TOON encoder/decoder
│   │   ├── encoder.py                # Object to TOON conversion
│   │   ├── decoder.py                # TOON to Python objects
│   │   ├── file_handler.py           # TOON file I/O
│   │   └── *_parser.py               # Parsing components
│   ├── nix/                          # Nix expression handling
│   │   ├── codec.py                  # Nix codec
│   │   ├── encoder.py                # Python to Nix conversion
│   │   └── parser.py                 # Nix expression parser
│   ├── toml/                         # TOML file handling
│   │   ├── file_handler.py           # TOML file I/O
│   │   └── pyproject_toml.py         # pyproject.toml parser
│   ├── yamls/                        # YAML file handling
│   │   └── file_handler.py           # YAML file I/O with safe loading
│   ├── jsons/                        # JSON file handling
│   │   └── file_handler.py           # JSON file I/O
│   ├── jsonl/                        # JSON Lines handling
│   │   ├── file_handler.py           # JSONL streaming I/O
│   │   └── utils.py                  # JSONL helpers
│   ├── text/                         # Text file handling
│   │   ├── file_handler.py           # Text file I/O
│   │   └── bytes_handler.py          # Binary file I/O
│   ├── xmls/                         # XML processing
│   │   ├── file_handler.py           # XML file I/O
│   │   ├── base_worker.py            # XML parsing base
│   │   └── helpers.py                # XML utilities
│   ├── general/                      # Core file handling utilities
│   │   ├── base_file_handler.py      # Abstract file handler base class
│   │   ├── file_info.py              # File metadata and stats
│   │   ├── file_lock.py              # File locking for concurrent access
│   │   ├── mock_text.py              # Mock text generation
│   │   └── textio_utility.py         # Text I/O helpers
│   ├── common.py                     # Shared constants and utilities
│   └── config.py                     # Pydantic-based configuration
├── tests/                            # Comprehensive test suite (416+ tests)
│   ├── pythons/                      # Python builder tests
│   ├── files/                        # File handler tests
│   └── test_*.py                     # Format-specific tests
├── examples/                         # Usage demonstrations
│   ├── builders_demo.py              # Python builder examples
│   ├── plugin_generator_demo.py      # Plugin registry generation
│   └── *_demo.py                     # Format-specific examples
└── config/                           # Development configuration
    ├── ruff.toml                     # Linting/formatting rules
    ├── pytest.ini                    # Test configuration
    └── codec_cub/                    # App configuration files
        ├── prod.toml
        └── test.toml
```

## Development Notes

- **Minimum Python Version**: 3.13
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`)
- **Modern Python**: Uses built-in types (`list`, `dict`) and `collections.abc` imports
- **Type Checking**: Full type hints with pyright in strict mode

## Pre-Commit Workflow

**CRITICAL: Always run these checks before committing code!**

### Required Steps Before Every Commit

1. **Activate virtual environment** (if not already active):
   ```bash
   source .venv/bin/activate
   ```

2. **Fix formatting and linting** (REQUIRED):
   ```bash
   nox -s ruff_fix
   ```
   - This runs both `ruff check --fix` and `ruff format`
   - Auto-fixes: import sorting, formatting, many linting issues
   - Will fail if there are unfixable linting errors (must be fixed manually)

3. **Run type checking** (REQUIRED):
   ```bash
   nox -s pyright
   ```
   - Must pass with zero errors
   - Project uses strict mode - all functions need type hints
   - Common fixes:
     - Missing return types: Add `-> ReturnType` to function signatures
     - Undefined names: Check imports are correct
     - Type narrowing: Use `isinstance()` checks or type guards

4. **Run tests** (REQUIRED):
   ```bash
   nox -s tests
   ```
   - All tests must pass before committing
   - Watch for test count changes (current: 416 tests)

### Common Issues and Solutions

**Ruff Issues:**
- **TID252 (relative imports)**: Use absolute imports from `codec_cub.*` instead of relative `from ..module`
  - Bad: `from ..helpers import foo`
  - Good: `from codec_cub.pythons.helpers import foo`
- **TC003 (type-checking imports)**: Move stdlib type-only imports into `TYPE_CHECKING` block
  - Works because `from __future__ import annotations` makes annotations strings
- **ARG002 (unused arguments)**: Add `# noqa: ARG002` if the argument is required by protocol/interface
- **F821 (undefined name)**: Missing import - add to top of file

**Pyright Issues:**
- **reportUndefinedVariable**: Import the name or check if it's in `TYPE_CHECKING` block (move out if used at runtime)
- **reportAttributeAccessIssue**: Object doesn't have that attribute - check object type or use `hasattr()` guard
- **reportGeneralTypeIssues**: Type mismatch - ensure function returns match declared return type

### Tool Usage Notes

**Ruff (`nox -s ruff_fix`):**
- Two-stage process: check/fix, then format
- Most issues auto-fixed (imports, formatting, simple linting)
- Some require manual intervention (logged to stdout)
- Exit code 1 = unfixable issues exist

**Pyright (`nox -s pyright`):**
- Zero tolerance - must have zero errors
- Uses `config/pyright.json` configuration
- Strict mode enabled - comprehensive type checking
- No auto-fix - all errors must be manually resolved

**Workflow Example:**
```bash
source .venv/bin/activate
nox -s ruff_fix      # Fix formatting/linting
nox -s pyright       # Check types
nox -s tests         # Run tests
git add .
git commit -m "..."
```
## Configuration

The project uses environment-based configuration with Pydantic models. Configuration files are located in the `config/codec_cub/` directory and support multiple environments (prod, test).

Key environment variables:
- `CODEC_CUB_ENV`: Set environment (prod/test)
- `CODEC_CUB_DEBUG`: Enable debug mode

