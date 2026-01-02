import os
import tomllib


def advanced_yaml_version() -> str:
    try:
        pyproject_path = os.path.join(os.path.dirname(__file__), "../../pyproject.toml")
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["project"]["version"]
    except Exception:
        # fallback to old version if pyproject.toml is missing or malformed
        return "Unknown due to internal error reading pyproject.toml"
