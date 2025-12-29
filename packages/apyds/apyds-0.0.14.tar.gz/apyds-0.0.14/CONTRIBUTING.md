# Contributing to DS

Thank you for your interest in contributing to DS! We welcome issues and pull requests from everyone.

This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Style](#code-style)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Running Tests](#running-tests)
- [Submitting Pull Requests](#submitting-pull-requests)
- [License](#license)

## Getting Started

DS is a deductive system for logical inference implemented in C++, with bindings for Python (via pybind11) and TypeScript/JavaScript (via Emscripten/WebAssembly).

To get started:

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ds.git
   cd ds
   ```
3. Set up your development environment (see below)

## Development Environment

### Prerequisites

- **C++**: C++20 compatible compiler (GCC 10+, Clang 10+, MSVC 2019+), CMake 3.30+
- **Python**: Python 3.11-3.14
- **TypeScript/JavaScript**: Node.js 20+, Emscripten SDK (for building WebAssembly)

### Building the Project

#### C++ Core Library

```bash
cmake -B build
cmake --build build
```

#### Python Package

```bash
uv sync --extra dev
```

#### TypeScript/JavaScript Package

Requires [Emscripten SDK](https://emscripten.org/docs/getting_started/downloads.html) to be installed.

```bash
npm install
npm run build
```

## Code Style

This project uses automated code formatting tools to ensure consistency. Please make sure your code follows these styles before submitting.

### C++

- Uses [clang-format](https://clang.llvm.org/docs/ClangFormat.html) for formatting
- Configuration is in `.clang-format`
- Run manually: `clang-format -i <file>`

### Python

- Uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Configuration is in `pyproject.toml`
- Run manually:
  ```bash
  ruff check --fix
  ruff format
  ```

### TypeScript/JavaScript

- Uses [Biome](https://biomejs.dev/) for linting and formatting
- Configuration is in `biome.json`
- Run manually: `npx @biomejs/biome check`

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run code quality checks automatically before each commit.

### Setup

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

The hooks will automatically run on staged files when you commit. To run all hooks manually:

```bash
pre-commit run --all-files
```

### Configured Hooks

- **clang-format**: Formats C/C++/CUDA files
- **ruff-check**: Lints Python files (with auto-fix)
- **ruff-format**: Formats Python files
- **biome-check**: Lints and formats TypeScript/JavaScript files

## Running Tests

### TypeScript/JavaScript

```bash
npm test
```

### Python

```bash
uv run pytest
```

### C++

```bash
cd build
ctest
```

## Submitting Pull Requests

1. Create a new branch for your changes

2. Make your changes and commit with a clear, descriptive commit message

3. Push to your fork and submit a pull request to the main repository

## License

By contributing to DS, you agree that your contributions will be licensed under the [GNU Affero General Public License v3.0 or later](LICENSE.md).
