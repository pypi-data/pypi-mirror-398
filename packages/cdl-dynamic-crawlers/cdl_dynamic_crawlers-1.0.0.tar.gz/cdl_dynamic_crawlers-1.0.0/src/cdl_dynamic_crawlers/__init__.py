from __future__ import annotations

import importlib.util
import inspect
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from cyberdrop_dl.crawlers.crawler import Crawler
    from cyberdrop_dl.managers.manager import Manager


def _import_crawlers(path: Path) -> Generator[type[Crawler]]:
    module_spec = importlib.util.spec_from_file_location(path.stem, path)
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module.__name__] = module
    module_spec.loader.exec_module(module)

    for _, cls in inspect.getmembers(
        module,
        lambda obj: (
            inspect.isclass(obj)
            and obj.__name__.endswith("Crawler")
            and obj.__name__ in getattr(module, "__all__", [obj.__name__])
            and obj.__module__.startswith(module.__name__)
            and not obj.__name__.startswith("_")
        ),
    ):
        yield cls


def main() -> Callable[[Manager], None]:
    return _load_crawlers


def _load_crawlers(manager: Manager) -> None:
    from cyberdrop_dl.scraper.scrape_mapper import register_crawler

    for file in (manager.path_manager.appdata / "crawlers").glob("*.py"):
        for crawler_cls in _import_crawlers(file):
            if crawler_cls.IS_GENERIC or crawler_cls.IS_ABC or crawler_cls.IS_FALLBACK_GENERIC:
                continue

            crawler = crawler_cls(manager)
            try:
                register_crawler(
                    manager.scrape_mapper.existing_crawlers, crawler, from_user="raise"
                )
            except ValueError:
                continue
