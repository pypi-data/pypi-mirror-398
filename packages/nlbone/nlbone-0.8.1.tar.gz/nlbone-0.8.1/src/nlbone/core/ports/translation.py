from abc import ABC, abstractmethod
from typing import Optional


class TranslationPort(ABC):
    @abstractmethod
    def translate(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        pass

    def __call__(self, key: str, locale: Optional[str] = None, **kwargs) -> Optional[str]:
        return self.translate(key, locale, **kwargs)
