"""Tests for migration functionality."""

import os
import shutil
import tempfile
from collections.abc import Generator

import pytest

from zecmf.migrations import setup_migrations


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing migrations."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_setup_migrations_creates_directory(temp_dir: str) -> None:
    """Test that setup_migrations creates the migrations directory."""
    # Call setup_migrations
    setup_migrations(destination_dir=temp_dir)

    # Check directory was created
    assert os.path.exists(temp_dir)

    # Check expected files were created
    assert os.path.exists(os.path.join(temp_dir, "env.py"))
    assert os.path.exists(os.path.join(temp_dir, "alembic.ini"))
    assert os.path.exists(os.path.join(temp_dir, "README"))
    assert os.path.exists(os.path.join(temp_dir, "script.py.mako"))


def test_setup_migrations_with_model_imports(temp_dir: str) -> None:
    """Test that setup_migrations adds model imports to env.py."""
    model_imports = [
        "from app.models.user import User",
        "from app.models.post import Post",
    ]

    # Call setup_migrations with model imports
    setup_migrations(destination_dir=temp_dir, models_import_statements=model_imports)

    # Read the env.py file
    env_py_path = os.path.join(temp_dir, "env.py")
    with open(env_py_path, encoding="utf-8") as f:
        env_py_content = f.read()

    # Check that model imports were added
    for import_stmt in model_imports:
        assert import_stmt in env_py_content
