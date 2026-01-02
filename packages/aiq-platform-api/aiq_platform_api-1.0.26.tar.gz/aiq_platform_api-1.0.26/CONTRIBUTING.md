# Contributing

⚠️ **BETA / EXPERIMENTAL PROJECT** ⚠️

This is an experimental project in active development. Features and APIs may change frequently.

## Quick Start

1. Fork and clone the repository
2. Create a new branch for your changes
3. Make your changes
4. Test with workflow tests (see below)
5. Run `make format && make ruff`
6. Submit a Pull Request

## Guidelines

**See `CLAUDE.md` for detailed coding standards.** Key principles:

- **Fail fast** - No defensive programming, let exceptions propagate
- **Customer workflows > Test coverage** - Focus on real use cases
- **F-strings** for all logging and string interpolation
- **Self-documenting code** - No useless comments or docstrings
- **Keep it simple** - Avoid over-engineering

## Testing

**Workflow tests are preferred over unit tests:**

```bash
# Run workflow tests (preferred)
poetry run python aiq_platform_api/scenario_use_cases.py
poetry run python aiq_platform_api/assessment_use_cases.py

# Code quality
make format && make ruff
```

Add new functionality by:
1. Adding methods to `core/*.py` modules
2. Adding wrapper functions to `*_use_cases.py`
3. Adding TestChoice enum and test function
4. Running the workflow test

## Publishing (Maintainers)

```bash
make install-dev                    # Install dev dependencies
poetry run python aiq_platform_api/scenario_use_cases.py  # Workflow test
make format && make ruff            # Code quality
make version-patch                  # Bump version
make publish                        # Publish to PyPI
```

## Questions?

Feedback: rajesh.sharma@attackiq.com | Access: Request invite to AttackIQ GitHub.