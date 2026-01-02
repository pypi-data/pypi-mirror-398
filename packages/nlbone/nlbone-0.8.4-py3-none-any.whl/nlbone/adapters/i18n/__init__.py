from pathlib import Path

from nlbone.config.settings import get_settings

from .engine import I18nAdapter
from .loaders import JSONFileLoader, CompositeLoader

loader = CompositeLoader()
loader.add_loader(JSONFileLoader(locales_path=Path(__file__).parent.joinpath("./locales").__str__()))
JSONFileLoader(locales_path=lambda: get_settings().PROJECT_LOCALE_PATH)
translator = I18nAdapter(loader=loader, default_locale="fa-IR")
