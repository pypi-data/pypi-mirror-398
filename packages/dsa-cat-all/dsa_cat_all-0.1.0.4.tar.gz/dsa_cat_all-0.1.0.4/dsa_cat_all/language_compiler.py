from json import load
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_translate(translates, language, text):
    return translates[text][language]
def language_compile():
    with open(BASE_DIR / "language.json", "r") as f:
        language = load(f)
    with open(BASE_DIR / "language", "r") as f:
        m = f.read()
    return (language, m)
def change_language(language):
    with open(BASE_DIR / "language", "w+") as f:
        f.write(language)