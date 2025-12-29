# pytest-forger

![](https://raw.githubusercontent.com/DaryllLorenzo/pytest-forger/main/images/pytest-forger.jpg)

> Version: 0.1.0 
> Status: **First functional release with CLI**

---

## What is pytest-forger?

pytest-forger is a Python tool designed to forge PyTest-ready tests from existing Python source code.

The goal of the project is to reduce the friction and boilerplate involved in writing tests by automatically generating test scaffolding and mocks based on the structure of your code, while keeping the developer fully in control of the final behavior.

---

## Project Vision

Writing tests is essential, but writing test boilerplate is often repetitive, time-consuming, and discouraging—especially in service-oriented architectures with repositories, external services, and layered dependencies.

pytest-forger aims to:

- Analyze Python source code statically
- Detect function and method dependencies
- Identify external boundaries (repositories, services, adapters)
- Automatically generate:
  - PyTest test files
  - Mocked dependencies
  - Executable test scaffolding

pytest-forger does not attempt to guess business logic or replace human reasoning.  
Instead, it focuses on automating the mechanical and structural parts of testing.

---

## Design Principles

pytest-forger is built around a few core principles:

- Automation without magic  
  Generated tests should be explicit, readable, and predictable.

- Structure over semantics  
  The tool understands code structure, not business intent.

- Mocks at the boundaries  
  External dependencies are mocked; internal logic remains real.

- Developer ownership  
  Generated tests are meant to be edited, extended, and owned by the developer.

---

## Intended Use Cases

pytest-forger is especially useful for:

- Service layers calling repositories or other services
- Legacy codebases with little or no test coverage
- Quickly bootstrapping tests for refactoring
- Teams that want consistency in test structure
- Developers who want to avoid repetitive PyTest boilerplate

---

## What pytest-forger Is *Not*

To set clear expectations, pytest-forger is not:

- A replacement for test design
- A business-logic inference engine
- A fully autonomous test generator
- A PyTest plugin (at least initially)

pytest-forger generates starting points, not perfect tests.

---

## Planned Capabilities (Future Versions)

These features are planned, not yet implemented:

- Static analysis of function and method call graphs
- Automatic mock generation for:
  - Repositories
  - External services
  - Imported functions
- Minimal factory generation based on return type hints
- PyTest-compatible test scaffolding
- Configurable mock policies

---

## Changelog

### [0.1.0] - 2025-12-26
#### Added
- Initial CLI implementation using Typer framework
- `ptf version` command to display project version and information
- `ptf forge <source_file.py>` command interface for test generation
- Complete argument parsing system with options:
  - `--function` / `-f` - Target specific function for test generation
  - `--output` / `-o` - Custom output directory for generated tests
  - `--overwrite` / `-w` - Overwrite existing test files
  - `--verbose` / `-v` - Enable detailed output for debugging
- Project structure with `src/` layout
- PyPI-ready packaging configuration in `pyproject.toml`
- Dependencies: `pytest>=7.4.0`, `typer>=0.9.0`

#### Notes
- `ptf forge` currently provides the interface without actual code analysis
- This release establishes the foundation for implementing test generation
- Installation via `pip install -e .` for development

---

### 🔧 Coming in v0.2.0
- Actual Python source code analysis
- Test skeleton generation from functions
- Basic test file creation with proper imports
- Support for simple function signatures
---

## Philosophy

pytest-forger exists to answer one simple question:

> *“How much of testing can we automate without lying to ourselves?”*

The answer is: a lot of the boring parts.

---

## License

MIT License 

---

## Disclaimer

pytest-forger is an early-stage project under active design.  
Breaking changes are expected in early versions.

---

*Forge tests, not excuses.*