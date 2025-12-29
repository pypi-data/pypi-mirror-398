import os
import re
from pathlib import Path
import logging


def find_env_file(start_path=None, env_filename=".env"):
    """
    Find the nearest .env file starting from the start_path upwards.

    :param start_path: The directory to start searching from. Defaults to current working directory.
    :param env_filename: The name of the environment file. Defaults to ".env".
    :return: Path to the .env file if found, else None.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    for parent in [start_path] + list(start_path.parents):
        env_path = parent / env_filename
        if env_path.is_file():
            return env_path
    return None


def parse_env_file(env_path):
    """
    Parse the .env file and return a dictionary of environment variables.

    :param env_path: Path to the .env file.
    :return: Dictionary of environment variables.
    """
    env_vars = {}
    with open(env_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$', line)
            if match:
                key, value = match.groups()
                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                env_vars[key] = os.path.expandvars(value)
    return env_vars


def load_env(env_path=None, env_filename=".env", strict=False):
    """
    Load environment variables from a .env file into os.environ.

    :param env_path: Optional path to the .env file.
    :param env_filename: The name of the environment file if env_path is not provided.
    :param strict: If True, raises FileNotFoundError when no env file is found. Otherwise just logs a warning.
    """
    if env_path:
        env_file = Path(env_path)
        if not env_file.is_file():
            raise FileNotFoundError(f"No such .env file: {env_path}")
    else:
        env_file = find_env_file(env_filename=env_filename)
        if not env_file:
            if strict:
                raise FileNotFoundError(f"No .env file found starting from {Path.cwd()}")
            else:
                logging.warning(f"No .env file found starting from {Path.cwd()}")
                return  # Early return when no env file is found and not in strict mode

    env_vars = parse_env_file(env_file)
    os.environ.update(env_vars)