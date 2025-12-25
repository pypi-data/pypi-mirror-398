# Podkit - Simple Container Management Library

A Python library for sandboxed execution in Docker containers with backend abstraction (Kubernetes-ready)

## Features

- **Backend Abstraction**: Works with Docker initially, designed for easy Kubernetes migration
- **Container Management**: Container operations
- **Session Management**: Track user sessions with container lifecycle management



## Development Setup

### Prerequisites

- Docker
- uv

### Installation

```bash
./scripts/install.sh
```

## Running Tests

### Integration Tests (Recommended)

Run tests in Docker container (most realistic):

```bash
./scripts/test.sh
```

This will:
1. Build the test runner container with all dependencies
2. Mount the Docker socket and test workspace
3. Run pytest with the integration tests
4. Clean up automatically

### Local Testing (Development)

For faster iteration during development:

```bash
# Start test container and keep it running
docker-compose run --rm test-runner bash

# Inside the container, run tests
pytest tests/integration/test_integration_happy_path.py -v

# Or run specific tests
pytest tests/integration/test_integration_happy_path.py::TestPodkitIntegrationHappyPath::test_01_backend_initialized -v
```

### Linting

```bash
./scripts/lint.sh         # Check only
./scripts/lint.sh --fix   # Auto-fix issues
```

This runs `ruff` and `pylint` for code checking and formatting.
