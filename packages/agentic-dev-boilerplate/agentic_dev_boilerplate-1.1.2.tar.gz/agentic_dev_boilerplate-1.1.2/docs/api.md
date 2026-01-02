# API Documentation

## Overview

The `agentic-dev-boilerplate` package provides a command-line tool for generating customized agentic development workflows tailored to specific projects.

## Installation

```bash
pip install agentic-dev-boilerplate
```

## CLI Usage

### Basic Usage

```bash
agentic-dev-boilerplate --schema project-schema.yaml --output ./my-project
```

### Options

- `--schema, -s`: Path to the project schema YAML file (default: `project-schema.yaml`)
- `--output, -o`: Output directory for generated boilerplate (default: current directory)

### Example

```bash
# Generate boilerplate for a Python web application
agentic-dev-boilerplate -s my-app-schema.yaml -o ./my-app-boilerplate
```

## Schema Format

The project schema is a YAML file that defines the project structure, agents, workflows, and configuration.

### Required Fields

- `project`: Project metadata (name, description, repository)
- `languages`: Programming languages and frameworks
- `agents`: List of agents with roles and scopes
- `workflows`: Enabled workflow features

### Example Schema

```yaml
project:
  name: "my-project"
  description: "A sample project"
  version: "1.0.0"

languages:
  - name: "python"
    version: "3.11"
    frameworks: ["fastapi", "sqlalchemy"]

agents:
  - role: "software-engineer"
    enabled: true
    scope: ["code-implementation", "refactoring"]

workflows:
  pr_automation: true
  ci_cd: true
```

## Generated Structure

The tool generates a complete project structure including:

- Agent instruction files
- GitHub workflows
- Utility scripts
- Task tracking system
- Documentation
- CI/CD configuration

## Agents

### Available Agents

- **Planner**: Task decomposition and roadmap generation
- **Tester**: Validation suites and test execution
- **Debugger**: Root cause analysis and patch development
- **Deployer**: Production deployment and rollback orchestration
- **Systems Engineer**: Hardware emulation and infrastructure
- **DevOps Specialist**: Infrastructure automation and CI/CD
- **Orchestrator**: Multi-agent coordination
- **Software Engineer**: Code implementation and architecture design
- **AI Engineer**: ML model development and AI integration

### Customizing Agents

Modify the `agents` section in your schema to enable/disable agents and customize their scopes.