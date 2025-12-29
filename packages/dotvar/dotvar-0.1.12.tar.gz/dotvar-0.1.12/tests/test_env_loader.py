# tests/test_env_loader.py

import os
import tempfile

import pytest

from dotvar import load_env


@pytest.fixture
def temp_env_file():
    # Create a temporary .env file
    temp_dir = tempfile.TemporaryDirectory()
    env_path = os.path.join(temp_dir.name, ".env")
    with open(env_path, "w") as f:
        f.write("""
        # Sample .env file
        DATABASE_URL=postgres://user:password@localhost:5432/dbname
        SECRET_KEY='s3cr3t'
        DEBUG=True
        API_KEY=${SECRET_KEY}_api
        
        ML_LOGGER_ROOT=http://your-host.mit.edu:8000
        ML_LOGGER_USER=geyang
        ML_LOGGER_TOKEN=
        PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
        """)
    yield env_path
    temp_dir.cleanup()


def test_load_env(temp_env_file):
    load_env(env_path=temp_env_file)

    assert os.environ.get("DATABASE_URL") == "postgres://user:password@localhost:5432/dbname"
    assert os.environ.get("SECRET_KEY") == "s3cr3t"
    assert os.environ.get("DEBUG") == "True"


def test_load_env_with_url(temp_env_file):
    load_env(env_path=temp_env_file)

    assert os.environ.get("ML_LOGGER_ROOT") == "http://your-host.mit.edu:8000"
    assert os.environ.get("ML_LOGGER_USER") == "geyang"
    assert os.environ.get("ML_LOGGER_TOKEN") == ""
    assert os.environ.get("PYTORCH_CUDA_ALLOC_CONF") == "expandable_segments:True"


def test_env_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_env(env_path="/non/existent/path/.env")


def test_load_env_with_nested_variables(temp_env_file):
    load_env(env_path=temp_env_file)
    assert os.environ.get("API_KEY") == "s3cr3t_api"


