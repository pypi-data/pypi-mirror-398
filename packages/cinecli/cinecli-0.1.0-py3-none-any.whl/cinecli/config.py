from pathlib import Path
import tomllib

CONFIG_PATH = Path.home() / ".config" / "cinecli" / "config.toml"

def load_config():
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

