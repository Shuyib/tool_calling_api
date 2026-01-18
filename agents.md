# Agents Conventions

This document harmonizes Makefile-derived developer conventions with augmentative best-practices inspired by Noah Gift / Pragmatic AI Labs and the fast.ai developer style guide. It is written to be non-breaking and augmentive: preserve existing Makefile behavior while recommending optional improvements for reproducibility, discoverability, CI parity, and notebook hygiene.

## Purpose
Provide a concise, actionable reference for:
- How agents (developers, automation) should run tasks via Makefile.
- How to keep local development and CI behavior consistent.
- Notebook and coding style guidance informed by Pragmatic AI Labs (Noah Gift) and fast.ai.

## Quick summary of existing Makefile behavior (source: repo Makefile)
- Virtual env: `.venv`, activate script at `.venv/bin/activate`
- Key variables: `PYTHON=.venv/bin/python3`, `PIP=.venv/bin/pip3`, `DOCKER_IMAGE_NAME`, `DOCKER_IMAGE_VERSION`, `DOCKER_IMAGE_TAG`
- Standard targets present: `venv/bin/activate`, `activate`, `install`, `docstring`, `format`, `clean`, `lint`, `test`
- `.ONESHELL:` and `.DEFAULT_GOAL := all` are used.

## Core agent recommendations (non-breaking, augmentive)
1. Use venv binaries directly inside Make targets and CI:
   - Prefer `.venv/bin/python` and `.venv/bin/pip` in recipes to avoid relying on shell activation persistence.
2. Keep targets idempotent and declarative:
   - Make sure `install`, `format`, `lint`, and `test` can be re-run safely.
3. Add discoverability and CI-parity targets (suggested, optional):
   - `.PHONY: help ci install-dev` and a `help` target that lists commands.
   - `ci` target runs same steps as CI (e.g., `install-dev format lint test`).
4. Separate runtime and dev dependencies:
   - Introduce `requirements-dev.txt` and `install-dev` target to install linting/test tools.
5. Makefile UX improvements inspired by Pragmatic AI Labs:
   - Add helpful echo messages, fail-fast settings (e.g., `set -euo pipefail` in multi-line recipes), and explicit `.PHONY`.
6. Docker ergonomics:
   - Use `DOCKER_IMAGE_TAG` for build/push targets and consider deriving version from git tags in CI.
7. Notebook and experiment hygiene (fast.ai-aligned):
   - Keep notebooks runnable top-to-bottom; move production logic into `.py` modules.
   - Strip outputs before commit (use `nbstripout`, `jupytext`, or pre-commit hooks).
   - Store experiment artifacts under `runs/` or `artifacts/`.

## Suggested non-breaking Makefile snippets (optional additions)
- help, venv, install-dev, ci, docker-build examples using `.venv/bin/*` binaries and `.PHONY` list (see repository README or conventions for full snippet).

## Linting, formatting, docstrings, testing
- Format: keep `black *.py utils/*.py tests/*.py` but run via `.venv/bin/black` in CI or `install-dev`.
- Docstrings: `pyment -w -o numpydoc *.py` remains valid—document usage in CONTRIBUTING.
- Lint: keep `pylint --disable=R,C --errors-only *.py` for errors-only mode; consider `lint-full` for stricter checks.
- Test: use `pytest` invocation from Makefile but ensure small, deterministic tests for CI.

## Reproducibility & releases
- Consider `pip-compile`/lockfiles or poetry for reproducible builds when releasing.
- Add `bump-version` or derive Docker tag from git in CI for consistent releases.

## Notebook- and fast.ai-specific guidance
- Prefer short, testable functions; avoid heavy computations committed to notebooks.
- Convert critical notebook logic to modules and add unit tests.
- Use `pre-commit` with nbstripout/jupytext and black/isort to keep diffs clean.

## Documentation & contribution
- Keep this file updated when adding Makefile targets or changing developer workflow.
- Add `CONTRIBUTING.md` pointing to `make help`, `make ci`, and notebook guidelines.

## References and sources
- fast.ai developer style guide: https://docs.fast.ai/dev/style.html
- Pragmatic AI Labs / Noah Gift: https://paiml.com/ and https://noahgift.com/
