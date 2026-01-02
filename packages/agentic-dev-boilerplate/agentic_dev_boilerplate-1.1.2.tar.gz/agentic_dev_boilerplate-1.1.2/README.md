# Agentic Dev Boilerplate

A comprehensive template system for generating agentic development workflows and automation infrastructure.

**Version**: 1.1.1  
**Repository**: https://github.com/tzervas/agentic-dev-boilerplate

## Overview

This project provides a complete foundation for building agentic development systems with automated multi-agent coordination, intelligent task tracking, and comprehensive CI/CD pipelines. It includes specialized agents for planning, testing, debugging, deployment, and system engineering, all working together to streamline development workflows.

## Quick Start

### Installation

#### From PyPI (Recommended)
```bash
pip install agentic-dev-boilerplate
```

#### From Source
```bash
git clone https://github.com/tzervas/agentic-dev-boilerplate
cd agentic-dev-boilerplate
pip install -e .
```

### Generate Boilerplate

Create a new project with the CLI:

```bash
# Generate boilerplate for your project
agentic-dev-boilerplate --schema project-schema.yaml --output ./my-project

# Or use short options
agentic-dev-boilerplate -s my-schema.yaml -o ./my-project
```

## Prerequisites

- **Python** 3.11 or later
- **Git** 2.30+ (for version control)
- **GPG** (for commit signing)

## Development Setup

1. **Install UV (fast Python package manager)**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**
   ```bash
   git clone https://github.com/tzervas/agentic-dev-boilerplate
   cd agentic-dev-boilerplate
   ```

3. **Set up development environment**
   ```bash
   uv venv
   uv pip install -e .
   ```

4. **Configure Git**
   ```bash
   python scripts/git_setup.py --setup
   ```

## Testing

### Comprehensive Test Suite

Run the complete validation suite:

```bash
./test-package.sh
```

### Docker Testing

For isolated testing and validation:

```bash
# Build and run tests
docker-compose up --build

# Or build and test manually
docker build -t agentic-boilerplate-test .
docker run --rm agentic-boilerplate-test
```

## Development Workflow

### 1. Task Planning
Use the planner agent to break down features and create implementation roadmaps. Tasks are tracked in `tasking/tracker.yaml` with context files stored in `tasking/context/`.

### 2. Implementation
- Create feature branches: `git checkout -b feature/task-name`
- Implement changes following project standards
- Write comprehensive tests for new functionality

### 3. Testing & Validation
```bash
# Run validation suite
python scripts/validation_scripts.py

# Run tests
uv run pytest
```

### 4. Create Pull Request
```bash
# Create PR with automation
python scripts/create_pr_local.py

# Or use GitHub CLI
gh pr create --fill
```

### 5. Code Review
Pull requests are automatically enriched with labels and milestones. Validation runs automatically on PR events to ensure code quality and standards compliance.

## Multi-Agent Coordination

The system supports collaborative problem-solving through coordinated multi-agent workflows.

### Starting Multi-Agent Sessions
```bash
# Solve complex problems with multiple agents
python scripts/multi_agent_solver.py \
  --problem "Implement user authentication system" \
  --agents planner tester debugger deployer \
  --consensus-threshold 0.8
```

### Agent Coordination Features
- **Orchestrated Problem Decomposition**: Complex tasks are automatically broken down into manageable components
- **Cross-Agent Validation**: Solutions are validated by multiple specialized agents
- **Consensus Building**: Team agreement on optimal approaches and solutions
- **Collaborative Tracking**: Shared progress monitoring and status updates
- **Coordinated Execution**: Synchronized implementation across all participating agents

### Available Agents

- **Planner**: Task decomposition, roadmap generation, and agent routing
- **Tester**: Validation suites, test execution, and result analysis
- **Debugger**: Root cause analysis, log processing, and patch development
- **Deployer**: Production deployment, rollback orchestration, and change management
- **Systems Engineer**: Hardware emulation, IOMMU/VFIO configuration, and GPU passthrough
- **DevOps Specialist**: Infrastructure automation, CI/CD pipelines, and network orchestration
- **Orchestrator**: Multi-agent coordination, collaborative problem-solving, and team consensus
- **Software Engineer**: Code implementation, refactoring, and architecture design
- **AI Engineer**: ML model development, AI integration, and data pipeline optimization

### GitHub Integration
Label issues or pull requests to trigger multi-agent coordination:
- `testing` → Involves tester agent
- `debug` → Involves debugger agent
- `deploy` → Involves deployer agent
- `infra` → Involves systems engineer and DevOps specialist

## Project Structure

```
├── .github/
│   ├── instructions/          # Agent instruction files
│   ├── prompts/              # Reusable prompt templates
│   ├── scripts/              # PR automation scripts
│   └── workflows/            # GitHub Actions CI/CD
├── scripts/                  # Utility scripts
├── tasking/                  # Task tracking system
│   ├── tracker.yaml         # Main task tracker
│   ├── context/             # Task context files
│   └── plan.md              # Project roadmap
├── docs/                    # Documentation
├── src/                     # Source code
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
└── README.md
```

## Agent System

### Core Agents

- **Planner**: Task decomposition, roadmap generation, and agent routing
- **Tester**: Validation suites, test execution, and result analysis
- **Debugger**: Root cause analysis, log processing, and patch development
- **Deployer**: Production deployment, rollback orchestration, and change management
- **Systems Engineer**: Hardware emulation, IOMMU/VFIO configuration, and GPU passthrough
- **DevOps Specialist**: Infrastructure automation, CI/CD pipelines, and network orchestration
- **Orchestrator**: Multi-agent coordination, collaborative problem-solving, and team consensus
- **Software Engineer**: Code implementation, refactoring, and architecture design
- **AI Engineer**: ML model development, AI integration, and data pipeline optimization

### Agent Instructions
Each agent has specialized instructions in `.github/instructions/` that define their role, responsibilities, workflow integration patterns, and success metrics.

## Quality Assurance

### Automated Validation
- **PR Automation**: Automatic labeling, milestone assignment, and issue linking
- **Code Quality**: Linting, formatting, and type checking
- **Testing**: Unit, integration, and system test coverage
- **Security**: Dependency scanning and vulnerability assessment

### Manual Reviews
- Code review requirements and standards
- Architecture decision documentation
- Performance and scalability considerations
- Security impact analysis

## Contributing

1. **Follow the workflow**: Use task tracking and agent coordination for all changes
2. **Write tests**: Ensure comprehensive test coverage for new functionality
3. **Sign commits**: All commits must be GPG signed for verification
4. **Create pull requests**: Use the automated PR creation tools

### Commit Standards
- Use conventional commit format: `type(scope): description`
- Sign all commits with GPG: `git commit -S`
- Reference task IDs in commit messages when applicable

### Pull Request Requirements
- All automated validation checks must pass
- Appropriate test coverage maintained
- Documentation updated for any user-facing changes
- Task tracker updated with completion status

## CI/CD Pipeline

### Pipeline Stages
- **Validate**: Code linting, testing, and security scanning
- **Build**: Package building and artifact creation
- **Deploy**: Staging deployment and production releases

### Quality Gates
- Code linting and formatting checks
- Test execution with coverage requirements
- Security vulnerability scanning
- Minimum 80% code coverage threshold

## Security

- **Commit Signing**: All commits must be GPG signed for authenticity
- **Dependencies**: Regular security scanning and dependency updates
- **Secrets**: Automated detection and prevention of exposed secrets

## Documentation

- **API Reference**: Comprehensive API documentation
- **User Guides**: Setup and usage instructions
- **Contributing Guide**: Development workflow and standards

## Support

- **Issues**: Use GitHub issues with appropriate labels for bug reports and feature requests
- **Discussions**: Technical discussions and community Q&A
- **Documentation**: Comprehensive guides available in the `/docs` directory

## License

See LICENSE file for details.
