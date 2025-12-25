import argostranslate.package
import argostranslate.translate

def _ensure_arabic_package():
    # Check if ar->en is installed
    installed = argostranslate.translate.get_installed_languages()
    ar = next((l for l in installed if l.code == "ar"), None)
    en = next((l for l in installed if l.code == "en"), None)
    
    if not (ar and en and ar.get_translation(en)):
        # Need to download and install package
        argostranslate.package.update_package_index()
        available = argostranslate.package.get_available_packages()
        pkg = next((p for p in available if p.from_code == "ar" and p.to_code == "en"), None)
        if pkg:
            argostranslate.package.install_from_path(pkg.download())

def translate_arabic_to_english(text: str) -> str:
    _ensure_arabic_package()  # Must call this first
    return argostranslate.translate.translate(text, from_code="ar", to_code="en")