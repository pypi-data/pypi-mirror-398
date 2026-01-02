#!/bin/bash
# Comprehensive test script for agentic-dev-boilerplate
# This script validates the package functionality using UV

set -e

echo "🧪 Running comprehensive package tests with UV..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "Running: $test_name... "
    TESTS_TOTAL=$((TESTS_TOTAL + 1))

    if eval "$test_command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Output:"
        cat /tmp/test_output.log
        echo ""
    fi
}

# Set up UV environment
export PATH="/home/spooky/.local/bin:$PATH"

# Test 1: UV lock file exists and is valid
run_test "UV lock file validation" "uv lock --dry-run"

# Test 2: Package can be built
run_test "Package build" "uv build --wheel"

# Test 3: Create virtual environment and install
run_test "Virtual environment setup" "uv venv /tmp/test-venv"

# Test 4: Install package in venv
run_test "Package installation" "uv pip install --python /tmp/test-venv/bin/python ./dist/*.whl"

# Test 5: CLI help works
run_test "CLI help" "/tmp/test-venv/bin/agentic-dev-boilerplate --help"

# Test 6: Package generation works
run_test "Package generation" "mkdir -p /tmp/test-output && /tmp/test-venv/bin/agentic-dev-boilerplate -s project-schema.yaml -o /tmp/test-output"

# Test 7: Agent instruction files exist
run_test "Agent instructions count" "ls /tmp/test-output/.github/instructions/ | wc -l | grep -q '9'"

# Test 8: New agents are present
run_test "New agents present" "ls /tmp/test-output/.github/instructions/ | grep -c -E 'software-engineer|ai-engineer' | grep -q '2'"

# Test 9: Python imports work
run_test "Python imports" "/tmp/test-venv/bin/python -c 'from agentic_dev_boilerplate.generate_boilerplate import BoilerplateGenerator; print(\"Import successful\")'"

# Test 10: Schema validation
run_test "Schema validation" "/tmp/test-venv/bin/python -c '
import yaml
from agentic_dev_boilerplate.generate_boilerplate import BoilerplateGenerator
with open(\"project-schema.yaml\") as f:
    schema = yaml.safe_load(f)
gen = BoilerplateGenerator(\"project-schema.yaml\", \"/tmp/schema-test\")
assert len(gen.schema[\"agents\"]) == 9
assert gen.schema[\"project\"][\"version\"] == \"1.1.1\"
print(\"Schema validation passed\")
'"

# Test 11: Dependency versions are pinned
run_test "Dependency pinning" "grep -A 20 'dependencies = \[' pyproject.toml | grep -v '^\[' | grep -v '^]' | grep -v '^$' | grep -c '==' | grep -q '9'"

# Test 12: UV sync works
run_test "UV sync" "uv sync --dry-run"

# Cleanup
rm -rf /tmp/test-output /tmp/schema-test /tmp/test-venv /tmp/test_output.log

# Summary
echo ""
echo "📊 Test Results: $TESTS_PASSED/$TESTS_TOTAL tests passed"

if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
    echo -e "${GREEN}🎉 All tests passed! Package is stable and ready.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Please review the output above.${NC}"
    exit 1
fi