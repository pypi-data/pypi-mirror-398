"""Free Google Translate API for Python. Translates totally free of charge."""
__all__ = ['Translator', 'AsyncTranslator']
__version__ = '0.0.10'

from idioma.async_translator import AsyncTranslator
from idioma.constants import LANGCODES, LANGUAGES  # noqa
from idioma.translator import Translator
