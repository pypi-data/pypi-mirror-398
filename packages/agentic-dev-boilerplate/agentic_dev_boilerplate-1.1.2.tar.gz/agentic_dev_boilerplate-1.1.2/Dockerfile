# Use Python 3.11 Alpine image for lightweight container
FROM python:3.11-alpine

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_CACHE_DIR=/tmp/uv-cache

# Install system dependencies
RUN apk add --no-cache \
    curl \
    git \
    && rm -rf /var/cache/apk/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy project files
COPY . .

# Create UV lock file and install dependencies
RUN uv lock

# Install the package in editable mode
RUN uv pip install --system -e .

# Run basic validation tests
RUN agentic-dev-boilerplate --help

# Test package generation
RUN mkdir -p /tmp/test-output && \
    agentic-dev-boilerplate -s project-schema.yaml -o /tmp/test-output && \
    ls -la /tmp/test-output/.github/instructions/ | grep -E "(software-engineer|ai-engineer)" && \
    echo "✅ Package generation test passed"

# Test Python import
RUN python3 -c "from agentic_dev_boilerplate.generate_boilerplate import BoilerplateGenerator; print('✅ Import test passed')"

# Test basic functionality
RUN python3 -c "\
import yaml; \
from agentic_dev_boilerplate.generate_boilerplate import BoilerplateGenerator; \
import tempfile; \
import os; \
\
# Test schema loading \
with open('project-schema.yaml', 'r') as f: \
    schema = yaml.safe_load(f); \
\
generator = BoilerplateGenerator('project-schema.yaml', '/tmp/schema-test'); \
loaded_schema = generator.schema; \
\
assert loaded_schema['project']['name'] == 'agentic-dev-boilerplate'; \
assert len([a for a in loaded_schema['agents'] if a['role'] in ['software-engineer', 'ai-engineer']]) == 2; \
print('✅ Schema loading and validation test passed'); \
"

# Clean up test artifacts
RUN rm -rf /tmp/test-output /tmp/schema-test

# Default command
CMD ["agentic-dev-boilerplate", "--help"]