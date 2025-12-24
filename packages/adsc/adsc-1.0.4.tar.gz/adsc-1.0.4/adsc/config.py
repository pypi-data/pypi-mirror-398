import json
from pathlib import Path

BASE_DIR = Path.home() / ".adsc"
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text())
    except Exception:
        return {}

def save_config(cfg):
    BASE_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def reset_all():
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
