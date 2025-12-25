from abc import abstractmethod
from typing import Callable, Optional
from pydantic import BaseModel, ConfigDict

from typing import Type

from ..api import ScoutAPI
from ..api.project_helpers import scout


class CrawlerConfiguration(BaseModel):
    model_config = ConfigDict(extra="allow")

    crawler_name: str
    important_document_masks: list[str] = ["*.*"]
    included_masks: list[str] = ["*.*"]
    excluded_masks: list[str] = []


class Crawler:
    def __init__(
        self,
        configuration: CrawlerConfiguration,
        on_url_found: Callable[[str, bool], None],
    ):
        self.on_url_found = on_url_found
        self.configuration = configuration
        pass

    @abstractmethod
    def crawl(self) -> None:
        pass

    @abstractmethod
    def download_url(self, url: str, local_file: str) -> str:
        pass


class CrawlerClassDecorator:
    _registered_crawlers: dict[str, Type[Crawler]]

    def __init__(self) -> None:
        from .crawlers_impl.sharepoint_crawler import SharepointCrawler

        self._registered_crawlers = {"Sharepoint": SharepointCrawler}

    def register(
        self,
        name: str,
    ) -> Callable[[Type[Crawler]], Type[Crawler]]:
        def decorator(cls: Type[Crawler]) -> Type[Crawler]:
            if not issubclass(cls, Crawler):
                raise TypeError(
                    f"Class '{cls.__name__}' cannot be registered: not a subclass of Crawler."
                )
            self._registered_crawlers[name] = cls
            return cls

        return decorator

    def create(
        self,
        crawler_configuration: CrawlerConfiguration,
        on_url_found: Optional[Callable[[str, bool], None]],
    ) -> Crawler:
        crawler_name = crawler_configuration.crawler_name
        crawler_type = self._registered_crawlers.get(crawler_name)
        if crawler_type is None:
            raise ValueError("Unable to find crawler named " + crawler_name)

        return crawler_type(
            crawler_configuration,
            on_url_found
            if on_url_found
            else AsynchronousIndexerCallback(crawler_configuration).on_url_found,
        )

    def crawl(self, crawler_configuration: CrawlerConfiguration) -> None:
        asyncronous = (
            scout.registered_functions.get("crawler_index_async_function") is not None
        )
        if not asyncronous:
            print(
                "Warning: Indexing Synchronously. Call `crawlers.set_index_asynchronous` at the root of your project to index Asynchronously."
            )
        callback = (
            AsynchronousIndexerCallback(crawler_configuration)
            if asyncronous
            else SynchronousIndexerCallback(crawler_configuration)
        )
        crawler = self.create(
            crawler_configuration=crawler_configuration,
            on_url_found=callback.on_url_found,
        )
        crawler.crawl()

    def index_document(
        self, url: str, is_important: bool, crawler_configuration_dict: dict
    ) -> dict:
        import os
        import tempfile
        import traceback
        from .indexers import indexers

        def empty_on_url_found(url: str, important: bool) -> None:
            pass

        crawler_configuration = CrawlerConfiguration.model_validate(
            crawler_configuration_dict
        )
        try:
            crawler = crawlers.create(
                crawler_configuration=crawler_configuration,
                on_url_found=empty_on_url_found,
            )

            with tempfile.TemporaryDirectory() as tmp_dir:
                local_file = os.path.join(tmp_dir, os.path.basename(url))
                remote_url = crawler.download_url(url, local_file)
                indexers.index_document(remote_url, local_file, is_important)
            return {"result": "Indexing completed"}
        except Exception as e:
            print(f"Error indexing {url}: {e}", traceback.format_exc())
            return {"error": f"Error indexing {url}: {e}"}

    def set_index_asynchronous(self) -> None:
        @scout.async_function(
            description="Index the content of a URL, NEVER CALL THIS FUNCTION UNLESS EXPLICITELY ASKED TO"
        )
        def crawler_index_async_function(
            url: str, is_important: bool, crawler_configuration_dict: dict
        ) -> dict:
            return crawlers.index_document(
                url, is_important, crawler_configuration_dict
            )


class SynchronousIndexerCallback:
    from .crawlers import CrawlerConfiguration

    def __init__(self, crawler_configuration: CrawlerConfiguration):
        self.crawler_configuration = crawler_configuration

    def on_url_found(self, url: str, is_important: bool) -> None:
        from .indexers import indexers

        if indexers.indexer_exists_for_file(url):
            crawlers.index_document(
                url, is_important, self.crawler_configuration.model_dump()
            )
        else:
            print("No indexer configured for " + url)


class AsynchronousIndexerCallback:
    from .crawlers import CrawlerConfiguration

    def __init__(self, crawler_configuration: CrawlerConfiguration):
        if scout.registered_functions.get("crawler_index_async_function") is None:
            print(
                "No async indexing function found. Call `crawlers.register_indexing_function()` in the global scope of your project to initialize it."
            )
        self.crawler_configuration = crawler_configuration

    def call_indexing_function(self, url: str, is_important: bool) -> None:
        class NoResponse(BaseModel):
            pass

        assistant_id = scout.context["SCOUT_ASSISTANT_ID"]
        payload = {
            "url": url,
            "is_important": is_important,
            "configuration_dict": self.crawler_configuration.model_dump(),
        }
        ScoutAPI().assistants.execute_function(
            assistant_id,
            "crawler_index_async_function",
            payload,
            response_model=NoResponse,
        )

    def on_url_found(self, url: str, is_important: bool) -> None:
        from .indexers import indexers

        if indexers.indexer_exists_for_file(url):
            self.call_indexing_function(url, is_important)
        else:
            print("No indexer configured for " + url)


crawlers = CrawlerClassDecorator()
