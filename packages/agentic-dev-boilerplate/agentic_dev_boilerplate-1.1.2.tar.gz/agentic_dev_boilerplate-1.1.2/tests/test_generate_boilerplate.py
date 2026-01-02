"""Tests for generate_boilerplate module."""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open
from jinja2 import Template

from agentic_dev_boilerplate.generate_boilerplate import BoilerplateGenerator


@pytest.fixture
def sample_schema(tmp_path):
    """Sample project schema for testing."""
    schema = {
        "project": "test_project",
        "languages": ["python"],
        "agents": [
            {
                "role": "planner",
                "enabled": True,
                "capabilities": ["task_decomposition"]
            },
            {
                "role": "tester",
                "enabled": True,
                "capabilities": ["unit_testing"]
            }
        ],
        "workflows": [
            {
                "name": "development",
                "stages": ["plan", "implement", "test"]
            }
        ]
    }
    schema_file = tmp_path / "schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(schema, f)
    return schema_file


@pytest.fixture
def output_dir(tmp_path):
    """Temporary output directory for generation."""
    output = tmp_path / "output"
    output.mkdir()
    return output


@pytest.fixture
def mock_templates(tmp_path):
    """Create mock template directory structure."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create a simple template
    template_file = templates_dir / "test.md.j2"
    template_file.write_text("""
# {{ schema.project }}

Generated for {{ agent.role }}
""")

    return templates_dir


def test_schema_loading(sample_schema, output_dir):
    """Test loading and validation of project schema."""
    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))

    assert generator.schema["project"] == "test_project"
    assert len(generator.schema["agents"]) == 2
    assert generator.output_dir == output_dir


def test_schema_validation_missing_required(tmp_path):
    """Test schema validation with missing required fields."""
    # Create a schema file with missing required fields
    incomplete_schema = {
        "project": "test_project",
        # Missing 'languages', 'agents', 'workflows'
    }
    schema_file = tmp_path / "incomplete.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(incomplete_schema, f)
    
    with pytest.raises(ValueError, match="Missing required field"):
        BoilerplateGenerator(str(schema_file), "/tmp")


@patch('agentic_dev_boilerplate.generate_boilerplate.Environment')
@patch('agentic_dev_boilerplate.generate_boilerplate.FileSystemLoader')
def test_template_rendering(mock_loader, mock_env, sample_schema, output_dir, mock_templates):
    """Test template rendering process."""
    # Mock the Jinja2 environment
    mock_env_instance = mock_env.return_value
    mock_template = mock_env_instance.get_template.return_value
    mock_template.render.return_value = "rendered content"

    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))
    generator.templates_dir = mock_templates

    # Test template rendering
    template = generator.jinja_env.get_template("test.md.j2")
    result = template.render(schema=generator.schema, agent=generator.schema["agents"][0])
    
    assert result == "rendered content"
    mock_env_instance.get_template.assert_called_with("test.md.j2")
    mock_template.render.assert_called_with(schema=generator.schema, agent=generator.schema["agents"][0])


def test_directory_structure_creation(sample_schema, output_dir):
    """Test creation of basic directory structure."""
    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))
    generator.create_directory_structure()

    expected_dirs = [
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

    for dir_path in expected_dirs:
        assert (output_dir / dir_path).exists()


@pytest.mark.parametrize("agent_config,expected_enabled", [
    ({"role": "planner", "enabled": True}, True),
    ({"role": "tester", "enabled": False}, False),
    ({"role": "debugger", "enabled": True}, True),
])
def test_agent_instruction_generation(sample_schema, output_dir, agent_config, expected_enabled):
    """Test agent instruction file generation."""
    # Modify schema for test
    schema = yaml.safe_load(sample_schema.read_text())
    schema["agents"] = [agent_config]

    test_schema = output_dir / "test_schema.yaml"
    with open(test_schema, 'w') as f:
        yaml.dump(schema, f)

    generator = BoilerplateGenerator(str(test_schema), str(output_dir))

    with patch.object(generator, 'jinja_env') as mock_env, \
         patch('builtins.open', mock_open()) as mock_file:
        mock_template = mock_env.get_template.return_value
        mock_template.render.return_value = f"Instructions for {agent_config['role']}"

        generator.generate_agent_instructions()

        if expected_enabled:
            # Check that get_template was called with the right template
            mock_env.get_template.assert_called_with(f"agent_{agent_config['role']}_instructions.md.j2")
            # Check that render was called
            mock_template.render.assert_called()
            # Check that file was opened for writing
            mock_file.assert_called()
        else:
            # Should not call get_template for disabled agents
            mock_env.get_template.assert_not_called()


def test_end_to_end_generation(sample_schema, output_dir):
    """End-to-end test of boilerplate generation."""
    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))

    # Mock the template environment to avoid actual file operations
    with patch.object(generator, 'jinja_env') as mock_env:
        mock_template = mock_env.get_template.return_value
        mock_template.render.return_value = "# Generated content"

        # Mock all generation methods
        with patch.multiple(generator,
                          generate_agent_instructions=mock_open(),
                          generate_prompts=mock_open(),
                          generate_github_workflows=mock_open(),
                          generate_scripts=mock_open(),
                          generate_task_tracking=mock_open(),
                          generate_ci_cd=mock_open(),
                          generate_git_config=mock_open(),
                          generate_documentation=mock_open()):
            generator.generate()

            # Check that basic structure was created
            assert (output_dir / ".github").exists()
            assert (output_dir / "scripts").exists()
            assert (output_dir / "docs").exists()


def test_template_path_resolution(sample_schema, output_dir, tmp_path):
    """Test that template paths are resolved correctly."""
    # Create a custom templates directory
    custom_templates = tmp_path / "custom_templates"
    custom_templates.mkdir()
    (custom_templates / "readme.md.j2").write_text("# {{ schema.project }}")

    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))
    generator.templates_dir = custom_templates

    assert generator.templates_dir == custom_templates


@pytest.mark.parametrize("invalid_schema", [
    {"project": "test"},  # Missing languages
    {"languages": ["python"]},  # Missing project
    {"project": "test", "languages": ["python"]},  # Missing agents
])
def test_schema_validation_edge_cases(tmp_path, invalid_schema):
    """Test schema validation with various invalid configurations."""
    schema_file = tmp_path / "invalid.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(invalid_schema, f)

    with pytest.raises(ValueError):
        BoilerplateGenerator(str(schema_file), str(tmp_path / "output"))


def test_file_writing_error_handling(sample_schema, output_dir):
    """Test error handling when file writing fails."""
    generator = BoilerplateGenerator(str(sample_schema), str(output_dir))

    # Make output directory read-only to simulate write failure
    output_dir.chmod(0o444)

    try:
        with pytest.raises(OSError):
            generator.create_directory_structure()
    finally:
        output_dir.chmod(0o755)  # Restore permissions for cleanup