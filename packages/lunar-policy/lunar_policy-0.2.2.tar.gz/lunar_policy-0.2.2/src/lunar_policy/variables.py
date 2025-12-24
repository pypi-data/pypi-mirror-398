import os

prefix = 'LUNAR_VAR_'


def variable(var_key):
    for env_key, value in os.environ.items():
        if env_key.startswith(prefix):
            trimmed_key = env_key[len(prefix) :]  # Remove prefix
            if trimmed_key == var_key:
                return value

    return None


def variable_or_default(var_key, default):
    value = variable(var_key)
    if value is None:
        return default
    return value
