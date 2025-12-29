# Contributing to Zoho Projects SDK

Thank you for your interest in contributing! This project aims to provide a modern, asynchronous, and type-safe Python SDK for the Zoho Projects API V3. Contributions of any size are welcome—from typo fixes to new features.

## Getting Started

1. **Fork the repository** and clone your fork locally.
2. **Create a virtual environment** and install dependencies:

   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .[dev]
   ```

3. **Configure environment variables** required for integration tests by copying `.env.example` (if present) or setting variables manually.
4. **Create a feature branch** for your work.

## Development Guidelines

- **Type Checking:** Run `uv run mypy` to ensure the codebase remains type-safe.
- **Linting:** Use `uv run flake8`, `uv run isort .`, and `uv run black .` to keep the code clean and consistent.
- **Static Analysis:** Run `uv run pylint` to catch additional issues.
- **Testing:** All changes must include or update automated tests. Run the test suite with:

  ```bash
  uv run pytest
  ```

  Coverage is required to stay at 100% (`--cov-fail-under=100`). Add targeted unit or integration tests as needed.

- **Asynchronous Code:** Prefer async/await patterns and `httpx.AsyncClient` to preserve the SDK's async-first design.
- **Documentation:** Update docstrings, README snippets, or examples when behavior changes.

## Commit & PR Process

1. Keep commits focused; avoid bundling unrelated changes.
2. Follow the conventional commit style when possible (e.g., `feat: add task filtering`).
3. Ensure your branch is up to date with `main` before opening a pull request.
4. In your pull request description:
   - Summarize the change.
   - Reference related issues (e.g., `Closes #123`).
   - Describe testing performed (commands and results).

## Reporting Issues

When filing an issue, include:

- A clear description of the problem.
- Steps to reproduce (if applicable).
- Expected vs. actual behavior.
- Environment details (Python version, OS, etc.).

## Security

If you discover a security vulnerability, please contact the maintainer directly rather than filing a public issue. We will coordinate a fix and disclosure timeline together.

## Code of Conduct

Please review and follow our [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project, you agree to uphold a welcoming and respectful community.

We appreciate your contributions and look forward to collaborating with you!
