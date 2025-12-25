# pytest-forger

> Version: 0.0.1  
> Status: Early placeholder release (name reservation on PyPI)

---

## What is pytest-forger?

pytest-forger is a Python tool designed to forge PyTest-ready tests from existing Python source code.

The goal of the project is to reduce the friction and boilerplate involved in writing tests by automatically generating test scaffolding and mocks based on the structure of your code, while keeping the developer fully in control of the final behavior.

This initial release (**v0.0.1**) exists primarily to reserve the project name and clearly define the vision and scope of the project.

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
- CLI interface for test generation
- Configurable mock policies
- Optional integrations with LLMs for test suggestions (future)

---

## Current Status

Version 0.0.1
- Placeholder release
- Name reservation on PyPI
- No functional implementation yet
- API and architecture subject to change

Development will begin after this initial release.

---

## Roadmap (High-Level)

- 0.1.x — Core static analysis and test scaffolding
- 0.2.x — Mock generation and configuration
- 0.3.x — Factories and improved type handling
- 0.4.x+ — Advanced features and integrations

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