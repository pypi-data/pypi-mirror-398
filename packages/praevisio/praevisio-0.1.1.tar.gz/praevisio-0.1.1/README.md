# praevisio

A CLI tool for AI governance through verifiable promises.

This repository follows Readme-Driven Development and an outside-in approach. The white paper is the source of truth for behavior and outcomes we intend to deliver; we implement from the boundary inward until the tool matches the spec.

- White paper: docs/white-paper.md (rendered by Sphinx)
- Built docs entry point: docs/index.md

## Quickstart (uv)

0) Install uv (see https://docs.astral.sh/uv/)

1) Create a virtual environment and install dependencies

- uv venv
- uv sync --all-groups  # installs docs dependencies too

2) Build the docs

- uv run sphinx-build -b html docs docs/_build/html
- Open docs/_build/html/index.html in your browser

## Alternative (pip/venv)

1) Create and activate a virtual environment

- macOS/Linux
  - python3 -m venv .venv
  - source .venv/bin/activate
- Windows (PowerShell)
  - py -3 -m venv .venv
  - .venv\Scripts\Activate.ps1

2) Install documentation dependencies

- pip install -r requirements.txt

3) Build the docs

- make -C docs html
- Open docs/_build/html/index.html in your browser

## Build and publish (uv)

- Build artifacts (sdist/wheel):
  - uv build
- Publish to PyPI (requires a token):
  - uv publish --token $PYPI_API_TOKEN

## Architecture overview

Layers
- Domain (src/praevisio/domain): Core concepts and rules
  - Entities: Hook, HookResult, ValidationRule, CommitContext
  - Value Objects: HookType, ExitCode, FilePattern
  - Services: HookSelectionService (type filtering, dependency ordering, file pattern matching)
  - Ports: PromiseRepository, GitRepository, ProcessExecutor, FileSystemService, ConfigLoader
- Application (src/praevisio/application): Use cases/orchestration
  - HookOrchestrationService (hook_service.py): run hooks of a given HookType in correct order
  - PromiseService (promise_service.py): register and persist promises
  - ConfigurationService: load .praevisio.yaml into domain Configuration
  - InstallationService: write a default .praevisio.yaml
  - ValidationService: validate configuration & hook definitions
  - services.py: compatibility re-exports for older imports
- Infrastructure (src/praevisio/infrastructure): Adapters to ports
  - git.py (InMemoryGitRepository), process.py (RecordingProcessExecutor), filesystem.py (LocalFileSystemService), config.py (YamlConfigLoader, InMemoryConfigLoader)
  - Planned: ApiClient adapter(s)
- Presentation (src/praevisio/presentation): CLI and other interfaces
  - Typer-based CLI (praevisio). Commands map to application services

Configuration as a domain concept
- Canonical file: .praevisio.yaml
- Example:

  hooks:
    - id: example-lint
      name: Example Lint
      type: pre-commit
      command: ["echo", "lint"]
      patterns: ["**/*.py"]
      depends_on: []
      enabled: true
      file_scoped: true

Error handling
- ConfigurationInvalidException thrown by ValidationService
- Hook results carry ExitCode; future HookFailedException can be added for richer flow control

Dependency injection
- Application services accept ports via constructor injection for easy testing and swapping infrastructure adapters.

## BDD with Behave

- Install dev dependencies (includes behave):
  - uv sync --group dev  # or uv sync --all-groups
- Run the feature tests:
  - uv run behave -f progress

Example feature implemented
- Run pre-commit hooks: Skip hooks when no files match pattern
  - Given a repository with staged Python files (only .py)
  - And a hook configured for "*.js"
  - When I run pre-commit hooks
  - Then the hook should be skipped

Architecture notes:
- The project uses a layered architecture:
  - domain: core business objects and abstractions (no infra/presentation deps)
  - application: orchestrates use cases via domain and ports
  - infrastructure: adapter implementations (e.g., repositories)
  - presentation: CLI/HTTP adapters (to be added)
- Application services return domain objects or simple data structures, keeping them reusable across interfaces.

CLI entry point
- praevisio (Typer-based):
  - uv run praevisio install        # writes a default .praevisio.yaml
  - uv run praevisio pre-commit     # loads config, validates, runs pre-commit hooks
  - uv run praevisio evaluate-commit path/to/commit  # MVP evaluation (credence + verdict)
  - python -m praevisio             # equivalent entry point

Outside-in MVP flow with a separate lab repo (praevisio-test)
- In praevisio/: install as editable so the CLI and module are available to the lab
  - pip install -e .
- In praevisio-test/: write Behave tests that call the CLI, e.g.:
  - praevisio evaluate-commit commits/compliant/c1
- Minimal evaluation implemented:
  - Reads app/src/llm_client.py in the commit directory
  - If it contains a log(...) call → Credence 0.97 → Verdict green
  - Otherwise → Credence 0.42 → Verdict red


## Development approach

- Readme-Driven Development: We capture intent and interfaces up front in this README and the white paper. We will keep both current as we iterate.
- Outside-in: We will define user-visible CLI behavior first, then drive implementation via tests and thin slices until the internals satisfy the external contracts.
- Documentation-first: Sphinx is set up from day one; every significant change should be reflected in the docs.

## Documentation system

- Sphinx with MyST Markdown allows us to keep the white paper in Markdown while using Sphinx features.
- Theme: sphinx_rtd_theme
- Extensions enabled for future self-documentation work:
  - autodoc and napoleon (for API docs from docstrings)
  - viewcode (source links)
  - todo (TODO directives can be toggled in output)
  - autosectionlabel (stable xrefs)
  - intersphinx (cross-project linking)

Structure:
- docs/index.md: Site landing page and ToC
- docs/white-paper.md: Includes the white_paper.md via Sphinx include
- white_paper.md: Your authored white paper at the repo root

Build commands:
- make -C docs html
- Or directly: sphinx-build -b html docs docs/_build/html

## Next steps (planned)

- Project skeleton for the CLI (src/ layout, package metadata)
- Test harness and initial outside-in tests for first CLI story
- Self-documenting code via autodoc, with API docs published in docs/
- Continuous docs build (Read the Docs or CI job)

## Contributing

- Keep changes small and focused on an outcome.
- Update docs alongside code changes. If an interface changes, update examples in the README and white paper sections that reference it.
- Prefer tests that exercise the CLI surface area.

## License

- TBD by the repository owner. No license is included yet.
