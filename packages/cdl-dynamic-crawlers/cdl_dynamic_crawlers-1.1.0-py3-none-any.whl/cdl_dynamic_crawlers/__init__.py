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


def _load_crawlers(manager: Manager) -> None:
    for file in (manager.path_manager.appdata / "crawlers").glob("*.py"):
        for crawler_cls in _import_crawlers(file):
            if crawler_cls.IS_GENERIC or crawler_cls.IS_ABC or crawler_cls.IS_FALLBACK_GENERIC:
                continue

            crawler = crawler_cls(manager)
            try:
                _register_crawler(manager.scrape_mapper.existing_crawlers, crawler)
            except ValueError:
                continue


def _register_crawler(
    existing_crawlers: dict[str, Crawler],
    crawler: Crawler,
    include_generics: bool = False,
) -> None:
    from cyberdrop_dl.scraper.scrape_mapper import match_url_to_crawler
    from cyberdrop_dl.utils.logger import log

    if crawler.IS_FALLBACK_GENERIC:
        return
    if crawler.IS_GENERIC and include_generics:
        keys = (crawler.GENERIC_NAME,)
    else:
        keys = crawler.SCRAPE_MAPPER_KEYS

    for domain in keys:
        other = existing_crawlers.get(domain) or match_url_to_crawler(
            existing_crawlers, crawler.PRIMARY_URL
        )
        name = getattr(crawler, "GENERIC_NAME", crawler.NAME)

        if other:
            msg = (
                f"Unable to assign {domain = } to crawler {name} ({crawler.PRIMARY_URL}). "
                f"URL conflicts with URL format of builtin crawler {other.NAME}. "
                "URL will be ignored"
            )

            raise ValueError(msg)

        log(f"Successfully mapped {domain = } to crawler {name}")

        existing_crawlers[domain] = crawler


def main() -> Callable[[Manager], None]:
    return _load_crawlers
