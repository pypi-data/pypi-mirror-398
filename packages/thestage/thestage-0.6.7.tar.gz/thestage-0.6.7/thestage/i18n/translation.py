from typing import Optional

from python_gettext_translations.translations import translate

from thestage.config import THESTAGE_LOCAL_LANGUAGE


def __(original: str, placeholders: Optional[dict] = None) -> str:
    return translate(THESTAGE_LOCAL_LANGUAGE, original, placeholders)
