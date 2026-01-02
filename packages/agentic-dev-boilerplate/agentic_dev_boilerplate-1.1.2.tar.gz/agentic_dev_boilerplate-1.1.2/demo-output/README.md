# agentic-dev-boilerplate

Templatized repository for generating agentic development workflows and automations


**Version**: 1.1.1



**Repository**: https://github.com/tzervas/agentic-dev-boilerplate


## Overview

This project uses an agentic development workflow with automated:
- 🤖 Multi-agent task coordination and execution
- 🔄 PR creation, validation, and enrichment
- 📋 Intelligent task tracking and status management
- 🔐 Commit signing enforcement
- 🚀 CI/CD automation with comprehensive testing
- 📊 Quality assurance and validation

## Quick Start

### Prerequisites


- **Python** 3.11
 (uv)

- **Git** 2.30+
- **GPG** (for commit signing)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/tzervas/agentic-dev-boilerplate
   cd agentic-dev-boilerplate
   ```

2. **Set up development environment**
   ```bash
   python scripts/setup_uv.py
   ```

3. **Configure git**
   ```bash
   python scripts/git_setup.py --setup
   ```


4. **Set up commit signing**
   ```bash
   python scripts/setup_gpg.py
   ```


## Development Workflow

### 1. Task Planning
Use the planner agent to break down features:
```bash
# Tasks are tracked in tasking/tracker.yaml
# Context files are stored in tasking/context/
```

### 2. Implementation
- Create feature branches: `git checkout -b feature/task-name`
- Implement changes following project standards
- Write tests for new functionality

### 3. Testing & Validation
```bash
# Run validation suite
python scripts/validation_scripts.py

# Run language-specific tests


uv run pytest


```

### 4. Create PR
```bash
# Create PR with automation
python scripts/create_pr_local.py

# Or use GitHub CLI
gh pr create --fill
```

### 5. Code Review
- PRs are automatically enriched with labels and milestones
- Validation runs automatically on PR events
- Reviews ensure code quality and standards compliance

## Multi-Agent Coordination

This project supports collaborative problem-solving through multi-agent coordination:

### Starting Multi-Agent Sessions
```bash
# Solve complex problems with multiple agents
python scripts/multi_agent_solver.py \
  --problem "Implement user authentication system" \
  --agents planner tester debugger deployer \
  --consensus-threshold 0.8
```

### Agent Teamwork Features
- **🤖 Orchestrated Problem Decomposition**: Complex tasks automatically broken down
- **🔄 Cross-Agent Validation**: Solutions validated by multiple specialized agents
- **📊 Consensus Building**: Team agreement on optimal solutions
- **📋 Collaborative Tracking**: Shared progress and status updates
- **🚀 Coordinated Execution**: Synchronized implementation across agents

### Available Agents

- **Planner**: Task-Decomposition, Roadmap-Generation, Agent-Routing

- **Tester**: Validation-Suites, Test-Execution, Result-Analysis

- **Debugger**: Root-Cause-Analysis, Log-Processing, Patch-Development

- **Deployer**: Production-Deployment, Rollback-Orchestration, Change-Management

- **Systems-Engineer**: Hardware-Emulation, Iommu-Vfio, Gpu-Passthrough

- **Devops-Specialist**: Infrastructure-Automation, Ci-Cd, Network-Orchestration

- **Orchestrator**: Multi-Agent-Coordination, Collaborative-Problem-Solving, Team-Consensus

- **Software-Engineer**: Code-Implementation, Refactoring, Architecture-Design

- **Ai-Engineer**: Ml-Model-Development, Ai-Integration, Data-Pipeline-Optimization


### GitHub Integration
Label issues or PRs to trigger multi-agent coordination:
- `testing` → Involves tester agent
- `debug` → Involves debugger agent
- `deploy` → Involves deployer agent
- `infra` → Involves systems engineer and devops specialist

## Project Structure

```
├── .github/
│   ├── instructions/          # Agent instruction files
│   ├── prompts/              # Reusable prompt templates
│   ├── scripts/              # PR automation scripts
│   └── workflows/            # GitHub Actions
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


- **Planner**: Task-Decomposition, Roadmap-Generation, Agent-Routing



- **Tester**: Validation-Suites, Test-Execution, Result-Analysis



- **Debugger**: Root-Cause-Analysis, Log-Processing, Patch-Development



- **Deployer**: Production-Deployment, Rollback-Orchestration, Change-Management



- **Systems-Engineer**: Hardware-Emulation, Iommu-Vfio, Gpu-Passthrough



- **Devops-Specialist**: Infrastructure-Automation, Ci-Cd, Network-Orchestration



- **Orchestrator**: Multi-Agent-Coordination, Collaborative-Problem-Solving, Team-Consensus



- **Software-Engineer**: Code-Implementation, Refactoring, Architecture-Design



- **Ai-Engineer**: Ml-Model-Development, Ai-Integration, Data-Pipeline-Optimization



### Agent Instructions
Each agent has specialized instructions in `.github/instructions/` that define:
- Role and responsibilities
- When to use specific prompts
- Workflow integration patterns
- Success metrics

## Quality Assurance

### Automated Validation
- **PR Automation**: Labels, milestones, issue linking
- **Code Quality**: Linting, formatting, type checking
- **Testing**: Unit, integration, and system tests
- **Security**: Dependency scanning, vulnerability checks

### Manual Reviews
- Code review requirements
- Architecture decisions
- Performance considerations
- Security implications

## Contributing

1. **Follow the workflow**: Use task tracking and agent coordination
2. **Write tests**: Ensure adequate test coverage
3. **Sign commits**: All commits must be GPG signed
4. **Create PRs**: Use the automated PR creation tools

### Commit Standards
- Use conventional commit format: `type(scope): description`
- Sign all commits: `git commit -S`
- Reference task IDs in commit messages

### PR Requirements
- Automated validation must pass
- Appropriate test coverage
- Documentation updated
- Task tracker updated

## CI/CD Pipeline


### Pipeline Stages

- **Validate**: lint, test, security

- **Build**: build, package

- **Deploy**: deploy staging, deploy production



### Quality Gates

- Lint

- Test

- Security


- Minimum 80% code coverage


## Security


- **Commit Signing**: All commits must be GPG signed


- **Dependencies**: Regular security scanning and updates


- **Secrets**: Automated detection of exposed secrets


## Documentation

- **API Docs**: Manual maintenance
- **User Guides**: Comprehensive setup and usage instructions
- **Contributing**: Development workflow and standards

## Support

- **Issues**: Use GitHub issues with appropriate labels
- **Discussions**: Technical discussions and Q&A
- **Documentation**: Comprehensive guides in `/docs`

## License


See LICENSE file for details.
