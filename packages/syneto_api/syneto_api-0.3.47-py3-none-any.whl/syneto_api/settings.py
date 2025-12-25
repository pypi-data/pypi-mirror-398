import os
from dotenv import load_dotenv

load_dotenv()

bool_values = {"true": True, "yes": True, "false": False, "no": False}


def get_env_flag(env_key: str) -> bool:
    """
    Returns the parsed value of the given env. var (assumed of boolean type).
    The values "True" and "Yes" (case-insensitive) are parsed as True while
    everything else (including non-existent env. var) parses as False.
    """
    env_value = os.environ.get(env_key, "")
    return bool_values.get(env_value.lower()) is True


def get_env_int(env_key, default=0) -> int:
    """
    Returns the parsed value of the given env. var (assumed of integer type).
    If the env. var does not exist, the given default is returned. If the env. var value
    fails to parse, a ValueError is raised.
    """
    env_value = os.environ.get(env_key, f"{default}")
    return int(env_value)


def get_env_string(env_key, default="") -> str:
    """
    Returns the associated os.environ value for the specified value as a string.
    """
    env_value = os.environ.get(env_key, f"{default}")
    return env_value


def get_root_path():
    root_path_env = os.environ.get("ROOT_PATH", "") or ""
    return "/" + root_path_env.strip("/")
