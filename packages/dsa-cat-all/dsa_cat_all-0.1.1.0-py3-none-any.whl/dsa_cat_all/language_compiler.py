from json import load, dump
from pathlib import Path
import sys
import subprocess
from .settings import *


if get_settings()["auto_translate"]:
    try:
        from argostranslate import translate, package
    except ImportError:
        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "argostranslate"
        ])
        from argostranslate import translate, package
    import os
    def argos_translate_via_en(text: str, from_lang: str, to_lang: str) -> str:
        """
        Переводит текст с любого языка на любой язык через английский (en),
        если прямой перевод недоступен.
        """
    
        def ensure_translation(src, dst):
            translate.load_installed_languages()
            languages = translate.get_installed_languages()
    
            src_lang = next((l for l in languages if l.code == src), None)
            dst_lang = next((l for l in languages if l.code == dst), None)
    
            if src_lang and dst_lang:
                tr = src_lang.get_translation(dst_lang)
                if tr:
                    return tr
    
            package.update_package_index()
            available = package.get_available_packages()
    
            pkg = next(
                (p for p in available if p.from_code == src and p.to_code == dst),
                None
            )
    
            if not pkg:
                return None
    
            path = pkg.download()
            package.install_from_path(path)
    
            translate.load_installed_languages()
            languages = translate.get_installed_languages()
            src_lang = next(l for l in languages if l.code == src)
            dst_lang = next(l for l in languages if l.code == dst)
    
            return src_lang.get_translation(dst_lang)
        direct = ensure_translation(from_lang, to_lang)
        if direct:
            return direct.translate(text)
        to_en = ensure_translation(from_lang, "en")
        from_en = ensure_translation("en", to_lang)
    
        if not to_en or not from_en:
            raise ValueError(f"Невозможно перевести {from_lang} → {to_lang} даже через en")
    
        intermediate = to_en.translate(text)
        return from_en.translate(intermediate)
    def argos_translate(text: str, from_lang: str, to_lang: str) -> str:
        """
        text       — текст для перевода
        from_lang  — код языка источника (например: 'ru', 'en', 'de', 'fr')
        to_lang    — код языка назначения
        """
        translate.load_installed_languages()
        languages = translate.get_installed_languages()
        from_language = next((l for l in languages if l.code == from_lang), None)
        to_language = next((l for l in languages if l.code == to_lang), None)
        if from_language is None or to_language is None:
            package.update_package_index()
            available_packages = package.get_available_packages()
            pkg = next(
                (p for p in available_packages
                 if p.from_code == from_lang and p.to_code == to_lang),
                None
            )
            if pkg is None:
                raise ValueError(f"Нет модели перевода {from_lang} → {to_lang}")
            download_path = pkg.download()
            package.install_from_path(download_path)
            translate.load_installed_languages()
            languages = translate.get_installed_languages()
            from_language = next(l for l in languages if l.code == from_lang)
            to_language = next(l for l in languages if l.code == to_lang)
        translation = from_language.get_translation(to_language)
        return translation.translate(text)
else:
    def argos_translate(text: str, from_lang: str, to_lang: str) -> str:
        raise WindowsError("Please use set_setting(\"auto_translate\", 1) to use auto translation.")
    def argos_translate_via_en(text: str, from_lang: str, to_lang: str) -> str:
        raise WindowsError("Please use set_setting(\"auto_translate\", 1) to use auto translation.")
def get_translate(text):
    translates, language = language_compile()
    m = list(translates.items())[:]
    if text not in translates:
        try:
            translates[text] = {"ru": text, "en": argos_translate_via_en(text, "ru", "en")}
        except:
            raise WindowsError("Please use set_setting(\"auto_translate\", 1) to use auto translation.")
    if language not in translates[text]:
        try:
            translates[text][language] = argos_translate_via_en(text, "ru", language)
        except:
            raise WindowsError("Please use set_setting(\"auto_translate\", 1) to use auto translation.")
    if m != translates:
        with open(BASE_DIR / f"language.json", "r", encoding="utf-8") as f:
            p = load(f)
            for i, i2 in translates.items():
                p[i] = i2
        with open(BASE_DIR / f"language.json", "w+", encoding="utf-8", newline="") as f:
            dump(p, f)
    return translates[text][language]
def language_compile():
    with open(BASE_DIR / "language.json", "r") as f:
        language = load(f)
    return (language, get_settings()["language"])
def change_language(language):
    with open(BASE_DIR / "language", "w+") as f:
        f.write(language)
