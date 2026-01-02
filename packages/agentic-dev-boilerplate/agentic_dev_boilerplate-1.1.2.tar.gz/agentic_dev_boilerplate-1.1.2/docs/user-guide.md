# User Guide

## Getting Started

This guide will help you get started with the `agentic-dev-boilerplate` package to generate customized development workflows for your projects.

## Installation

### From PyPI

```bash
pip install agentic-dev-boilerplate
```

### From Source

```bash
git clone https://github.com/tzervas/agentic-dev-boilerplate
cd agentic-dev-boilerplate
pip install -e .
```

## Creating a Project Schema

Before generating boilerplate, you need to create a project schema YAML file that defines your project's requirements.

### Basic Schema Structure

```yaml
project:
  name: "my-awesome-project"
  description: "A description of what your project does"
  repository: "https://github.com/username/my-awesome-project"
  version: "1.0.0"

languages:
  - name: "python"
    version: "3.11"
    frameworks: ["fastapi", "pydantic"]
    package_manager: "uv"
    testing: ["pytest"]
    linting: ["black", "isort"]

agents:
  - role: "planner"
    enabled: true
    scope: ["task-decomposition", "roadmap-generation"]
  - role: "software-engineer"
    enabled: true
    scope: ["code-implementation", "refactoring"]
  # Add other agents as needed

workflows:
  pr_automation: true
  task_tracking: true
  ci_cd: true
  multi_agent_coordination: true
```

### Advanced Configuration

You can customize various aspects of your project:

#### Git Configuration

```yaml
git:
  default_branch: "main"
  commit_signing: true
  pull_rebase: true
  aliases:
    co: "checkout"
    st: "status"
```

#### CI/CD Setup

```yaml
ci_cd:
  provider: "github_actions"
  phases:
    - name: "validate"
      trigger: ["push", "pull_request"]
      jobs: ["lint", "test"]
    - name: "deploy"
      trigger: ["release"]
      jobs: ["deploy_production"]
```

## Generating Boilerplate

Once you have your schema file, generate the boilerplate:

```bash
agentic-dev-boilerplate --schema my-schema.yaml --output ./my-project
```

This will create a complete project structure with:

- Agent instructions tailored to your project
- GitHub Actions workflows
- Utility scripts
- Task tracking system
- Documentation templates

## Using the Generated Boilerplate

### Setting Up the Project

1. Navigate to your generated project directory
2. Follow the setup instructions in the generated README.md
3. Configure your development environment
4. Set up Git and GPG signing if required

### Working with Agents

Each agent has specific instructions in `.github/instructions/` that define:

- When to use the agent
- What prompts to use for different scenarios
- How to coordinate with other agents
- Success criteria and metrics

### Task Tracking

Use the task tracking system in `tasking/`:

- `tracker.yaml`: Main task tracker
- `context/`: Task-specific context files
- `plan.md`: Project roadmap

### CI/CD Workflows

The generated GitHub Actions workflows provide:

- Automated testing and validation
- Code quality checks
- Security scanning
- Deployment automation

## Customization Examples

### Python Web API Project

```yaml
project:
  name: "my-api"
  description: "REST API for data processing"

languages:
  - name: "python"
    frameworks: ["fastapi", "sqlalchemy", "pydantic"]
    testing: ["pytest", "httpx"]

agents:
  - role: "software-engineer"
    enabled: true
  - role: "tester"
    enabled: true
  - role: "deployer"
    enabled: true

workflows:
  pr_automation: true
  ci_cd: true
```

### AI/ML Project

```yaml
project:
  name: "ml-pipeline"
  description: "Machine learning pipeline for predictions"

languages:
  - name: "python"
    frameworks: ["scikit-learn", "pandas", "jupyter"]

agents:
  - role: "ai-engineer"
    enabled: true
  - role: "software-engineer"
    enabled: true
  - role: "devops-specialist"
    enabled: true

workflows:
  task_tracking: true
  multi_agent_coordination: true
```

## Troubleshooting

### Common Issues

1. **Schema validation errors**: Ensure all required fields are present
2. **Missing templates**: Check that all referenced templates exist
3. **Permission errors**: Ensure write permissions in output directory

### Getting Help

- Check the generated README.md for project-specific instructions
- Review agent instructions in `.github/instructions/`
- Examine the schema file for configuration issues