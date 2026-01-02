#!/usr/bin/env python3
"""
Agentic Development Boilerplate Generator

Generates tailored development workflows and automations based on project schema.
"""

import os
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Environment, FileSystemLoader
import click

class BoilerplateGenerator:
    def __init__(self, schema_path: str, output_dir: str = None):
        self.schema_path = Path(schema_path)
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.schema = self.load_schema()
        self.templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(self.templates_dir)))

    def load_schema(self) -> Dict[str, Any]:
        """Load and validate the project schema."""
        with open(self.schema_path, 'r') as f:
            schema = yaml.safe_load(f)

        # Validate required fields
        required_fields = ['project', 'languages', 'agents', 'workflows']
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Missing required field: {field}")

        return schema

    def generate(self):
        """Generate the complete boilerplate."""
        click.echo("🚀 Generating agentic development boilerplate...")

        # Create output directory structure
        self.create_directory_structure()

        # Generate core components
        self.generate_agent_instructions()
        self.generate_prompts()
        self.generate_github_workflows()
        self.generate_scripts()
        self.generate_task_tracking()
        self.generate_ci_cd()
        self.generate_git_config()
        self.generate_documentation()

        click.echo("✅ Boilerplate generation complete!")

    def create_directory_structure(self):
        """Create the basic directory structure."""
        dirs = [
            ".github/instructions",
            ".github/prompts",
            ".github/scripts",
            ".github/workflows",
            "scripts",
            "docs",
            "templates",
            "examples",
            "tests"
        ]

        for dir_path in dirs:
            (self.output_dir / dir_path).mkdir(parents=True, exist_ok=True)

    def generate_agent_instructions(self):
        """Generate agent instruction files."""
        click.echo("🤖 Generating agent instructions...")

        agent_templates = {
            "planner": "agent_planner_instructions.md.j2",
            "tester": "agent_tester_instructions.md.j2",
            "debugger": "agent_debugger_instructions.md.j2",
            "deployer": "agent_deployer_instructions.md.j2",
            "systems-engineer": "agent_systems_engineer_instructions.md.j2",
            "devops-specialist": "agent_devops_specialist_instructions.md.j2",
            "orchestrator": "agent_orchestrator_instructions.md.j2",
            "software-engineer": "agent_software_engineer_instructions.md.j2",
            "ai-engineer": "agent_ai_engineer_instructions.md.j2"
        }

        for agent in self.schema.get('agents', []):
            if not agent.get('enabled', True):
                continue

            role = agent['role']
            if role in agent_templates:
                template = self.jinja_env.get_template(agent_templates[role])
                content = template.render(
                    schema=self.schema,
                    agent=agent
                )

                output_path = self.output_dir / ".github" / "instructions" / f"{role}.instructions.md"
                with open(output_path, 'w') as f:
                    f.write(content)

    def generate_prompts(self):
        """Generate reusable prompt templates."""
        click.echo("📝 Skipping prompt templates (not implemented)...")
        # TODO: Implement prompt template generation
        pass

    def generate_github_workflows(self):
        """Generate GitHub Actions workflows."""
        click.echo("🔄 Generating GitHub Actions workflows...")

        if self.schema.get('workflows', {}).get('pr_automation'):
            template = self.jinja_env.get_template("workflow_pr_automation.yml.j2")
            content = template.render(schema=self.schema)

            output_path = self.output_dir / ".github" / "workflows" / "pr-automation.yml"
            with open(output_path, 'w') as f:
                f.write(content)

        if self.schema.get('workflows', {}).get('ci_cd'):
            template = self.jinja_env.get_template("workflow_ci_cd.yml.j2")
            content = template.render(schema=self.schema)

            output_path = self.output_dir / ".github" / "workflows" / "ci-cd.yml"
            with open(output_path, 'w') as f:
                f.write(content)

        if self.schema.get('workflows', {}).get('multi_agent_coordination'):
            template = self.jinja_env.get_template("workflow_agent_coordination.yml.j2")
            content = template.render(schema=self.schema)

            output_path = self.output_dir / ".github" / "workflows" / "agent-coordination.yml"
            with open(output_path, 'w') as f:
                f.write(content)

    def generate_scripts(self):
        """Generate utility scripts."""
        click.echo("🛠️ Generating utility scripts...")

        scripts = [
            "create_pr_local.py",
            "git_setup.py",
            "validate_project.py",
            "setup_gpg.py",
            "setup_uv.py",
            "multi_agent_solver.py"
        ]

        for script_file in scripts:
            template_name = f"script_{script_file}.j2"
            try:
                template = self.jinja_env.get_template(template_name)
                content = template.render(schema=self.schema)

                output_path = self.output_dir / "scripts" / script_file
                with open(output_path, 'w') as f:
                    f.write(content)

                # Make scripts executable
                os.chmod(output_path, 0o755)
            except Exception as e:
                click.echo(f"⚠️ Skipping {script_file}: template {template_name} not found or error: {e}")

    def generate_task_tracking(self):
        """Generate task tracking system."""
        click.echo("📋 Generating task tracking system...")

        if self.schema.get('workflows', {}).get('task_tracking'):
            # Generate initial tracker
            tracker_data = {
                "version": "1.0",
                "project": self.schema['project']['name'],
                "tasks": [],
                "milestones": []
            }

            output_path = self.output_dir / "tasking" / "tracker.yaml"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, 'w') as f:
                yaml.dump(tracker_data, f, default_flow_style=False)

            # Generate plan template
            try:
                template = self.jinja_env.get_template("plan_template.md.j2")
                content = template.render(schema=self.schema)

                output_path = self.output_dir / "tasking" / "plan.md"
                with open(output_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                click.echo(f"⚠️ Skipping plan.md generation: template plan_template.md.j2 not found or error: {e}")

    def generate_ci_cd(self):
        """Generate CI/CD configuration."""
        click.echo("🚀 Generating CI/CD configuration...")

        ci_cd_config = self.schema.get('ci_cd', {})
        if ci_cd_config.get('provider') == 'github_actions':
            # Generate dependabot config
            if self.schema.get('workflows', {}).get('dependency_management'):
                dependabot_config = {
                    "version": 2,
                    "updates": []
                }

                for lang in self.schema.get('languages', []):
                    if lang['name'] == 'python':
                        dependabot_config['updates'].append({
                            "package-ecosystem": "pip",
                            "directory": "/",
                            "schedule": {"interval": "weekly"}
                        })
                    elif lang['name'] in ['javascript', 'typescript']:
                        dependabot_config['updates'].append({
                            "package-ecosystem": "npm",
                            "directory": "/",
                            "schedule": {"interval": "weekly"}
                        })

                output_path = self.output_dir / ".github" / "dependabot.yml"
                with open(output_path, 'w') as f:
                    yaml.dump(dependabot_config, f, default_flow_style=False)

    def generate_git_config(self):
        """Generate git configuration files."""
        click.echo("🔧 Generating git configuration...")

        # Generate .gitignore
        gitignore_content = self.generate_gitignore()
        output_path = self.output_dir / ".gitignore"
        with open(output_path, 'w') as f:
            f.write(gitignore_content)

        # Generate pyproject.toml for Python projects
        for lang in self.schema.get('languages', []):
            if lang['name'] == 'python':
                template = self.jinja_env.get_template("pyproject.toml.j2")
                content = template.render(schema=self.schema, lang=lang)

                output_path = self.output_dir / "pyproject.toml"
                with open(output_path, 'w') as f:
                    f.write(content)
                break  # Only generate one pyproject.toml

        # Generate pre-commit hooks if commit signing is enabled
        if self.schema.get('git', {}).get('commit_signing'):
            self.generate_pre_commit_hooks()

    def generate_gitignore(self) -> str:
        """Generate appropriate .gitignore based on languages."""
        gitignores = []

        # Base gitignore
        gitignores.append("""
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE files
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
*.log
logs/
""".strip())

        # Language-specific gitignores
        for lang in self.schema.get('languages', []):
            if lang['name'] == 'python':
                gitignores.append("""
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Testing
.coverage
.pytest_cache/
.tox/
""".strip())
            elif lang['name'] in ['javascript', 'typescript']:
                gitignores.append("""
# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# Build outputs
dist/
build/
.next/
.nuxt/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Testing
coverage/
.nyc_output/
""".strip())

        return '\n\n'.join(gitignores)

    def generate_pre_commit_hooks(self):
        """Generate pre-commit hooks for commit signing verification."""
        hook_content = """#!/bin/bash
# Pre-commit hook to verify commits are signed

# Check if commit is signed
if ! git verify-commit HEAD 2>/dev/null; then
    echo "❌ Commit is not signed!"
    echo "Please sign your commits by:"
    echo "  1. Setting up GPG: gpg --gen-key"
    echo "  2. Configuring git: git config --global user.signingkey <key-id>"
    echo "  3. Signing commits: git commit -S -m 'message'"
    echo "  Or amend this commit: git commit --amend -S"
    exit 1
fi

echo "✅ Commit is properly signed"
"""

        hooks_dir = self.output_dir / ".git" / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path = hooks_dir / "pre-commit"
        with open(hook_path, 'w') as f:
            f.write(hook_content)

        os.chmod(hook_path, 0o755)

    def generate_documentation(self):
        """Generate documentation files."""
        click.echo("📚 Generating documentation...")

        docs_config = self.schema.get('documentation', {})

        if docs_config.get('readme_generation'):
            try:
                template = self.jinja_env.get_template("README.md.j2")
                content = template.render(schema=self.schema)

                output_path = self.output_dir / "README.md"
                with open(output_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                click.echo(f"⚠️ Skipping README.md generation: template README.md.j2 not found or error: {e}")

        if docs_config.get('contributing_guide'):
            try:
                template = self.jinja_env.get_template("CONTRIBUTING.md.j2")
                content = template.render(schema=self.schema)

                output_path = self.output_dir / "CONTRIBUTING.md"
                with open(output_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                click.echo(f"⚠️ Skipping CONTRIBUTING.md generation: template CONTRIBUTING.md.j2 not found or error: {e}")

        if docs_config.get('changelog'):
            changelog_content = f"""# Changelog

All notable changes to {self.schema['project']['name']} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup with agentic development boilerplate
- Automated PR creation, validation, and enrichment
- Task tracking and status management
- Commit signing enforcement
- CI/CD automation with phased testing

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A
"""

            output_path = self.output_dir / "CHANGELOG.md"
            with open(output_path, 'w') as f:
                f.write(changelog_content)


@click.command()
@click.option('--schema', '-s', default='project-schema.yaml', help='Path to project schema file')
@click.option('--output', '-o', default=None, help='Output directory (default: current directory)')
def main(schema, output):
    """Generate agentic development boilerplate from schema."""
    try:
        generator = BoilerplateGenerator(schema, output)
        generator.generate()
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()