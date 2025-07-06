import pytest
import tempfile
import shutil
import os
from pathlib import Path


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "scenario: mark test as specific scenario")
    config.addinivalue_line("markers", "cloud: mark test as cloud provider specific")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")


@pytest.fixture(scope="session")
def test_data_dir():
    """Get the test data directory"""
    return Path(__file__).parent / "shared" / "fixtures"


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for tests"""
    temp_dir = tempfile.mkdtemp(prefix="xia_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_environment(monkeypatch):
    """Set up mock environment variables"""
    test_env = {
        "GCP_PROJECT": "test-project-123",
        "GITHUB_REPOSITORY": "test-user/test-repo",
        "GITHUB_ACTOR": "test-user",
        "COSMOS_NAME": "test-cosmos",
        "REALM_NAME": "test-realm",
        "FOUNDATION_NAME": "test-foundation"
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    
    return test_env


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test"""
    yield
    # Cleanup any .venv directories created during tests
    for item in Path.cwd().glob(".venv*"):
        if item.is_dir():
            shutil.rmtree(item, ignore_errors=True)