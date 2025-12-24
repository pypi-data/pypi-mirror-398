import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Callable, Union

logger = logging.getLogger(__name__)


class BaseLoader(ABC):
    @abstractmethod
    def load(self) -> Dict[str, Dict[str, str]]:
        pass


from typing import Callable, Union


class JSONFileLoader(BaseLoader):
    def __init__(self, locales_path: Union[str, Callable[[], str]]):
        self.locales_path_provider = locales_path

    def load(self) -> Dict[str, Dict[str, str]]:
        translations: Dict[str, Dict[str, str]] = {}

        if callable(self.locales_path_provider):
            path_str = self.locales_path_provider()
        else:
            path_str = self.locales_path_provider

        if not path_str:
            return translations

        path_obj = Path(path_str)

        if not path_obj.exists():
            return translations

        for file_path in path_obj.glob("*.json"):
            try:
                lang_code = file_path.stem
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                flat_data = self._flatten_dict(data)
                translations[lang_code] = flat_data

            except Exception as e:
                logger.error(f"Error loading locale {file_path}: {e}")

        return translations

    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, str]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, str(v)))
        return dict(items)


class CompositeLoader(BaseLoader):
    def __init__(self):
        self.loaders = []

    def add_loader(self, loader: BaseLoader):
        self.loaders.append(loader)

    def load(self) -> Dict[str, Dict[str, str]]:
        merged_translations: Dict[str, Dict[str, str]] = {}

        for loader in self.loaders:
            data = loader.load()
            for lang, keys in data.items():
                if lang not in merged_translations:
                    merged_translations[lang] = {}
                merged_translations[lang].update(keys)

        return merged_translations