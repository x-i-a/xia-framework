import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for tests"""
    temp_dir = tempfile.mkdtemp(prefix="xia_test_", dir=".")
    print(Path(temp_dir))
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)