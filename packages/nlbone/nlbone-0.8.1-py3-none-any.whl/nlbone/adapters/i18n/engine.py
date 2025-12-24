import logging
from typing import Dict, Optional

from nlbone.adapters.i18n.loaders import BaseLoader

from nlbone.core.ports.translation import TranslationPort

logger = logging.getLogger(__name__)


class I18nAdapter(TranslationPort):
    def __init__(self, loader: BaseLoader, default_locale: str = "fa-IR"):
        self.default_locale = default_locale
        self.loader = loader
        self._translations: Optional[Dict[str, Dict[str, str]]] = None

    def _ensure_loaded(self):
        if self._translations is None:
            self._translations = self.loader.load()

    def translate(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        target_locale = locale or self.default_locale
        try:
            self._ensure_loaded()

            locale_data = self._translations.get(target_locale, {})
            text = locale_data.get(key)

            if text is None:
                text = self._translations.get(self.default_locale, {}).get(key, key)

            if kwargs:
                try:
                    return text.format(**kwargs)
                except KeyError:
                    pass
            return text
        except:
            logger.exception("Failed to translate key '{}' to locale '{}'".format(key, target_locale))
            return key
