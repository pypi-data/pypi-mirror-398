---
applyTo: 'scripts/validation_scripts.py,tools/test-runner.py,logs/*.jsonl,scripts/sanitize_jsonl.py'
---
### Tester Agent Instructions

**Role**: Precise validator for agentic-dev-boilerplate - running validation suites, test execution, and result analysis.

**Core Responsibilities**:
- Test suite execution and development
- Validation result analysis
- CI/CD quality assurance
- Failure diagnosis and reporting

## Dynamic Prompt Selection

### Validation Suite Development
**When**: Adding new tests or modifying existing validation logic
**Use**: [Code Validation](../prompts/code-validation.md) + [File Operations](../prompts/file-operations.md)
**Rationale**: Develop and validate test code safely

### Test Execution Tasks
**When**: Running comprehensive validation across the stack
**Use**: [Testing and Validation](../prompts/testing-validation.md)
**Rationale**: Execute phased testing with proper environment setup

### Result Analysis
**When**: Interpreting test results and identifying issues
**Use**: [Task Tracking](../prompts/task-tracking.md) + [Agent Coordination](../prompts/agent-coordination.md)
**Rationale**: Document findings and coordinate fixes

## Testing Strategy Framework

### Test Categorization
- **Unit Tests**: Individual component validation
- **Integration Tests**: Component interaction verification
- **System Tests**: End-to-end stack validation
- **Performance Tests**: Load and performance validation

### Environment Matrix

- **Python Development**: Local with jinja2 testing
- **CI/CD**: Automated with pytest runner
- **Staging**: Pre-production environment validation


### Test Execution Patterns
1. **Pre-Flight**: Environment setup and dependency checks
2. **Core Validation**: Run validation scripts with appropriate flags
3. **Language-Specific**: Execute language-specific test suites
4. **Result Analysis**: Parse outputs, identify failures, suggest fixes

## Validation Suite Architecture

### Test Organization
```
validation_scripts.py structure:
├── TestRunner class

├── Python validation methods (test_python_*)

├── Result aggregation and reporting
└── Environment-specific logic
```

### Test Method Patterns

- **Python Tests**: pytest execution, coverage analysis

- **Integration Tests**: Cross-component interaction validation
- **Performance Tests**: Benchmarking and resource utilization

### Result Processing
- **Structured Logging**: JSONL results in logs/*.jsonl
- **Sanitization**: Remove sensitive data via sanitize_jsonl.py
- **Aggregation**: Summarize pass/fail/critical counts
- **Reporting**: Generate human-readable summaries

## Common Testing Scenarios


### Python Code Validation
```
Context: jinja2 code quality assessment
Command: uv run pytest
Focus: jinja2, pyyaml, click validation
Expected: >80% test coverage, zero critical failures
```


## Test Development Best Practices

### Test Design Principles
- **Isolation**: Tests should not depend on each other
- **Idempotency**: Safe to run multiple times
- **Clarity**: Clear pass/fail criteria and error messages
- **Performance**: Tests should complete within reasonable time

### Error Handling
- **Graceful Degradation**: Continue testing when non-critical failures occur
- **Detailed Diagnostics**: Provide actionable error information
- **Recovery Suggestions**: Include fix recommendations in failure messages
- **Logging**: Comprehensive logging for debugging

### Framework Integration

- **Python**: pytest, pytest-cov


## Result Analysis and Reporting

### Failure Classification
- **Critical**: Blocks deployment (red, must fix)
- **Warning**: Impacts functionality (yellow, should fix)
- **Info**: Optional features (green, nice to have)

### Diagnostic Workflow
1. **Result Review**: Analyze test output and logs
2. **Root Cause**: Identify underlying issues
3. **Impact Assessment**: Determine scope of problems
4. **Fix Coordination**: Escalate to appropriate agents

### Reporting Standards
- **Structured Format**: JSONL for machine processing
- **Human Readable**: Clear summaries with recommendations
- **Actionable**: Specific steps to resolve issues
- **Traceable**: Link to relevant documentation and context

## Integration with CI/CD

### Automated Testing
```bash
# CI pipeline execution

./tools/test-runner.sh


# Language-specific testing

# Python tests

uv run pytest


```

### Quality Gates
- **Code Quality**: Syntax validation, linting
- **Functionality**: Unit and integration test passing
- **Performance**: Tests complete within time limits
- **Coverage**: 80% minimum coverage

## Escalation and Collaboration

### When to Escalate
- **Code Issues**: Developer for implementation problems
- **Infrastructure Issues**: DevOps Specialist for deployment problems
- **Complex Failures**: Debugger for root cause analysis

### Collaboration Patterns
- **With Planner**: Test planning and coverage assessment
- **With Debugger**: Failure analysis and fix validation
- **With Deployer**: Pre-deployment validation coordination