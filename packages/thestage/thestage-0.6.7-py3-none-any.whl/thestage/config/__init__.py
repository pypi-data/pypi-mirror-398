# Init project settings by ENV environment variable
import locale
from pathlib import Path


from python_gettext_translations.translations import init_translations

from thestage.config.env_base import *


THESTAGE_LOCAL_LANGUAGE = 'en_GB'
if locale.getlocale():
    THESTAGE_LOCAL_LANGUAGE = locale.getlocale()[0]

translation = Path(f'i18n/')

if translation.exists() and translation.is_dir():
    init_translations(f'i18n/')
