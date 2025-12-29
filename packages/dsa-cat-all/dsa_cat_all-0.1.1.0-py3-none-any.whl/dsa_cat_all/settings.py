from json import load, dump
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_settings():
    with open(BASE_DIR / "settings.json", "r") as f:
        settings = load(f)
    return settings
def set_setting(key, value):
    with open(BASE_DIR / "settings.json", "r") as f:
        sett = load(f)
        sett[key] = value
    with open(BASE_DIR / "settings.json", "w") as f:
        dump(sett, f)