# E2E Tests for XIA Framework

This directory contains end-to-end tests that validate the XIA Framework functionality across different scopes and scenarios.

## Test Structure

```
tests/
├── README.md                           # This file
├── conftest.py                         # Global pytest configuration
├── requirements-test.txt               # Test dependencies
│
├── application/                        # Application-level E2E tests
│   ├── conftest.py                    # Application-specific fixtures
│   ├── scenarios/
│   │   └── data_pipeline/             # Data pipeline application scenario
│   │       ├── test_bigquery_pipeline.py
│   │       └── conftest.py
│   └── integration/                   # Cross-scenario integration tests
│
└── shared/                            # Shared test utilities
    ├── __init__.py
    ├── fixtures/                      # Common test data
    │   ├── configs/
    │   └── expected_outputs/
    ├── mocks/                         # Mock implementations
    │   ├── __init__.py
    │   ├── cloud_providers/
    │   └── tools/
    ├── utils/                         # Test utilities
    │   ├── __init__.py
    │   ├── test_helpers.py
    │   └── assertions.py
    └── base_test_cases.py             # Base test classes
```

## Running Tests

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Run all E2E tests
python -m pytest tests/ -v

# Run specific scenario
python -m pytest tests/application/scenarios/data_pipeline/ -v

# Run with specific markers
python -m pytest tests/ -m "data_pipeline and gcp" -v
```

## Current Focus: Data Pipeline Scenario

The data pipeline scenario validates the Quick Start guide for BigQuery-based data applications:

1. Repository setup and configuration initialization
2. Module initialization for GCS, GCP Project, GitHub integration
3. BigQuery module activation
4. Application creation with BigQuery dataset
5. Infrastructure deployment validation

## Test Markers

- `@pytest.mark.scenario("data_pipeline")`: Data pipeline tests
- `@pytest.mark.cloud("gcp")`: GCP-specific tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.integration`: Integration tests requiring multiple components