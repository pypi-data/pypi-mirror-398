# Contributing Guide

## Welcome

Thank you for your interest in contributing to `agentic-dev-boilerplate`! This guide will help you get started with development and contribution processes.

## Development Setup

### Prerequisites

- Python 3.11+
- Git
- GPG (for commit signing)

### Setup Steps

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/agentic-dev-boilerplate
   cd agentic-dev-boilerplate
   ```

2. **Set up development environment**
   ```bash
   python scripts/setup_uv.py
   ```

3. **Install in development mode**
   ```bash
   pip install -e .
   ```

4. **Configure Git**
   ```bash
   python scripts/git_setup.py --setup
   ```

## Development Workflow

### 1. Choose a Task

- Check existing issues or create a new one
- Use the task tracking system: `tasking/tracker.yaml`
- Coordinate with other contributors via issues

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes

- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes

```bash
git add .
git commit -S -m "feat: add your feature description"
```

Use conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `refactor:` for code refactoring
- `test:` for test additions

### 5. Create Pull Request

- Push your branch to GitHub
- Create a PR with a clear description
- Reference any related issues
- Wait for CI checks to pass

## Code Standards

### Python Code

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Keep line length under 88 characters (Black default)

### Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Use pytest for testing framework
- Mock external dependencies appropriately

### Documentation

- Update README.md for any user-facing changes
- Add docstrings to new functions/classes
- Update API documentation in `docs/api.md`
- Keep examples in `examples/` up to date

## Agent Development

### Adding New Agents

1. **Define the agent role and scope** in the schema
2. **Create instruction template** in `templates/agent_<role>_instructions.md.j2`
3. **Update generator** in `src/agentic_dev_boilerplate/generate_boilerplate.py`
4. **Add to schema** in `project-schema.yaml`
5. **Test generation** with the new agent

### Agent Instruction Template Format

```jinja
---
applyTo: 'file/patterns/to/apply/to'
---
### Agent Name Instructions

**Role**: Description of agent's role

**Core Responsibilities**:
- Responsibility 1
- Responsibility 2

## Dynamic Prompt Selection
[Content following existing patterns]
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=agentic_dev_boilerplate

# Run specific test
pytest tests/test_specific.py
```

### Testing Generated Boilerplate

```bash
# Generate test output
python -m agentic_dev_boilerplate.generate_boilerplate -s project-schema.yaml -o test-output

# Validate generated files
python scripts/validate_project.py
```

## Release Process

### Version Bumping

Update version in:
- `pyproject.toml`
- `project-schema.yaml`
- `CHANGELOG.md`

### Creating Releases

1. Create a release branch
2. Update version numbers
3. Update CHANGELOG.md
4. Create GitHub release
5. Publish to PyPI

## Communication

- Use GitHub issues for bug reports and feature requests
- Join discussions in pull request comments
- Follow the code of conduct

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for significant contributions
- GitHub's contributor insights
- Release notes

Thank you for contributing to `agentic-dev-boilerplate`!