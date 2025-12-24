import os


def find_dbt_profiles_file() -> str | None:
    paths = [
        "./profiles.yml",
        os.path.expanduser("~/.dbt/profiles.yml"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def find_snowflake_config_file() -> str | None:
    path = os.path.expanduser("~/.snowflake/config.toml")
    if os.path.exists(path):
        return path
    return None
