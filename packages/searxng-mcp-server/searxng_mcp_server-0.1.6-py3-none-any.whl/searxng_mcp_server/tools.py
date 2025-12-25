from typing import Any
from datetime import datetime, timezone
import tempfile

import asyncio
import httpx
from markitdown import MarkItDown

from searxng_mcp_server.config import Config
from searxng_mcp_server.log import get_logger
from searxng_mcp_server.models import (
    FetchUrlResult,
    FetchUrlResponse,
    ImageSearchResult,
    ImageSearchResponse,
    NewsSearchResult,
    NewsSearchResponse,
    VideoSearchResult,
    VideoSearchResponse,
    WebSearchResponse,
    WebSearchResult,
)

logger = get_logger(__name__)


class SearxNGClient:
    """Client for interacting with SearxNG API."""

    def __init__(self, config: Config) -> None:
        """Initialize the SearxNG client.

        Args:
            config: Configuration instance
        """
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.timeout, headers={"User-Agent": config.user_agent})

    async def _search(
        self,
        query: str,
        categories: list[str] | None = None,
        engines: list[str] | None = None,
        language: str | None = None,
        time_range: str | None = None,
        safesearch: bool = False,
        page: int = 1,
    ) -> dict[str, Any]:
        """Perform a search query on SearxNG.

        Args:
            query: Search query string
            categories: List of categories to search in (e.g., ['general', 'images', 'videos']).
                       Use None for default categories.
            engines: List of search engines to use (e.g., ['google', 'bing']).
                     Use None for default engine selection.
            language: Language code for results (e.g., 'en', 'en-US', 'fr', 'de').
                     Use None for no language preference.
            time_range: Time range filter ('day', 'week', 'month', 'year').
                       Use None for no time filtering.
            safesearch: Safe search filtering (True to enable, False to disable)
            page: Page number for pagination (starts at 1)

        Returns:
            Search results dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        params = {
            "q": query,
            "format": "json",
            "pageno": page,
        }

        if categories:
            params["categories"] = ",".join(categories)
        if engines:
            params["engines"] = ",".join(engines)
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range
        params["safesearch"] = 1 if safesearch else 0

        try:
            response = await self.client.get(
                f"{self.config.searxng_url}/search",
                params=params,  # type: ignore[arg-type]
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error("search request failed: %s", e)
            raise

    def _create_web_results(self, raw_results: dict[str, Any]) -> list[WebSearchResult]:
        """Convert SearxNG raw results to WebSearchResult models.

        Args:
            raw_results: Raw results from SearxNG API

        Returns:
            List of WebSearchResult objects
        """
        results = []
        for result in raw_results.get("results", []):
            published_date = None
            if result.get("publishedDate"):
                try:
                    parsed_date = datetime.fromisoformat(result["publishedDate"].replace("Z", "+00:00"))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    published_date = parsed_date.isoformat()
                except (ValueError, AttributeError):
                    pass

            search_result = WebSearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content"),
                engine=result.get("engine", "unknown"),
                score=result.get("score"),
                published_date=published_date,
            )
            results.append(search_result)

        return results

    def _create_image_results(self, raw_results: dict[str, Any]) -> list[ImageSearchResult]:
        """Convert SearxNG raw results to ImageResult models.

        Args:
            raw_results: Raw results from SearxNG API

        Returns:
            List of ImageResult objects
        """
        results = []
        for result in raw_results.get("results", []):
            published_date = None
            if result.get("publishedDate"):
                try:
                    parsed_date = datetime.fromisoformat(result["publishedDate"].replace("Z", "+00:00"))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    published_date = parsed_date.isoformat()
                except (ValueError, AttributeError):
                    pass

            thumbnail_url = result.get("thumbnail")
            if thumbnail_url and thumbnail_url.startswith("data:image"):
                thumbnail_url = None

            image_result = ImageSearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content"),
                engine=result.get("engine", "unknown"),
                score=result.get("score"),
                published_date=published_date,
                thumbnail_url=thumbnail_url,
                image_url=result.get("img_src"),
            )
            results.append(image_result)

        return results

    def _create_video_results(self, raw_results: dict[str, Any]) -> list[VideoSearchResult]:
        """Convert SearxNG raw results to VideoResult models.

        Args:
            raw_results: Raw results from SearxNG API

        Returns:
            List of VideoResult objects
        """
        results = []
        for result in raw_results.get("results", []):
            published_date = None
            if result.get("publishedDate"):
                try:
                    parsed_date = datetime.fromisoformat(result["publishedDate"].replace("Z", "+00:00"))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    published_date = parsed_date.isoformat()
                except (ValueError, AttributeError):
                    pass

            thumbnail_url = result.get("thumbnail")
            if thumbnail_url and thumbnail_url.startswith("data:image"):
                thumbnail_url = None

            video_result = VideoSearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content"),
                engine=result.get("engine", "unknown"),
                score=result.get("score"),
                published_date=published_date,
                thumbnail_url=thumbnail_url,
            )
            results.append(video_result)

        return results

    def _create_news_results(self, raw_results: dict[str, Any]) -> list[NewsSearchResult]:
        """Convert SearxNG raw results to NewsResult models.

        Args:
            raw_results: Raw results from SearxNG API

        Returns:
            List of NewsResult objects
        """
        results = []
        for result in raw_results.get("results", []):
            published_date = None
            if result.get("publishedDate"):
                try:
                    parsed_date = datetime.fromisoformat(result["publishedDate"].replace("Z", "+00:00"))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    published_date = parsed_date.isoformat()
                except (ValueError, AttributeError):
                    pass

            news_result = NewsSearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=result.get("content"),
                engine=result.get("engine", "unknown"),
                score=result.get("score"),
                published_date=published_date,
                source=result.get("engine", "unknown"),
            )
            results.append(news_result)

        return results

    async def search_web(
        self,
        query: str,
        language: str | None = None,
        time_range: str | None = None,
        safesearch: bool = False,
        max_results: int = 10,
    ) -> WebSearchResponse:
        """Search the web using SearxNG.

        Args:
            query: Search query string
            language: Language code for results (e.g., 'en', 'en-US', 'fr', 'de').
                     Use None for no language preference.
            time_range: Time range filter ('day', 'week', 'month', 'year').
                       Use None for no time filtering.
            safesearch: Safe search filtering (True to enable, False to disable)
            max_results: Maximum number of results to return (default: 10)

        Returns:
            WebSearchResponse with web search results
        """
        try:
            raw_results = await self._search(
                query=query,
                categories=None,
                engines=None,
                language=language,
                time_range=time_range,
                safesearch=safesearch,
            )

            search_results = self._create_web_results(raw_results)

            # Apply max_results limit
            if max_results > 0:
                search_results = search_results[:max_results]

            return WebSearchResponse(
                query=query,
                total_results=len(raw_results.get("results", [])),
                results=search_results,
                error=None,
            )
        except Exception as e:
            logger.error("search_web failed: %s", e)
            return WebSearchResponse(query=query, total_results=0, results=[], error=str(e))

    async def search_images(self, query: str, max_results: int = 10) -> ImageSearchResponse:
        """Search for images using SearxNG.

        Args:
            query: Image search query
            max_results: Maximum number of results to return (default: 10)

        Returns:
            ImageSearchResponse with image search results
        """
        try:
            raw_results = await self._search(query=query, categories=["images"])
            image_results = self._create_image_results(raw_results)

            # Apply max_results limit
            if max_results > 0:
                image_results = image_results[:max_results]

            return ImageSearchResponse(
                query=query,
                total_results=len(raw_results.get("results", [])),
                results=image_results,
                error=None,
            )
        except Exception as e:
            logger.error("search_images failed: %s", e)
            return ImageSearchResponse(query=query, total_results=0, results=[], error=str(e))

    async def search_videos(self, query: str, max_results: int = 10) -> VideoSearchResponse:
        """Search for videos using SearxNG.

        Args:
            query: Video search query
            max_results: Maximum number of results to return (default: 10)

        Returns:
            VideoSearchResponse with video search results
        """
        try:
            raw_results = await self._search(query=query, categories=["videos"])
            video_results = self._create_video_results(raw_results)

            # Apply max_results limit
            if max_results > 0:
                video_results = video_results[:max_results]

            return VideoSearchResponse(
                query=query,
                total_results=len(raw_results.get("results", [])),
                results=video_results,
                error=None,
            )
        except Exception as e:
            logger.error("search_videos failed: %s", e)
            return VideoSearchResponse(query=query, total_results=0, results=[], error=str(e))

    async def search_news(
        self,
        query: str,
        time_range: str | None = None,
        max_results: int = 10,
    ) -> NewsSearchResponse:
        """Search for news using SearxNG.

        Args:
            query: News search query
            time_range: Time range filter ('day', 'week', 'month', 'year').
                       Use None for no time filtering.
            max_results: Maximum number of results to return (default: 10)

        Returns:
            NewsSearchResponse with news search results
        """
        try:
            raw_results = await self._search(query=query, categories=["news"], time_range=time_range)
            news_results = self._create_news_results(raw_results)

            # Apply max_results limit
            if max_results > 0:
                news_results = news_results[:max_results]

            return NewsSearchResponse(
                query=query,
                total_results=len(raw_results.get("results", [])),
                results=news_results,
                error=None,
            )
        except Exception as e:
            logger.error("search_news failed: %s", e)
            return NewsSearchResponse(query=query, total_results=0, results=[], error=str(e))

    async def fetch_url(self, url: str) -> FetchUrlResponse:
        """
        Fetch content from a URL and convert it to markdown.

        Args:
            url: The URL to fetch and convert to markdown

        Returns:
            FetchUrlResponse with the markdown content and metadata
        """
        try:
            logger.info("fetching url: %s", url)

            # Download the content using httpx
            response = await self.client.get(url)
            response.raise_for_status()

            # Save to a temporary file for MarkItDown to process
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                temp_file.write(response.content)
                temp_file.flush()

                md = MarkItDown()

                # Convert the downloaded file using MarkItDown
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, md.convert, temp_file.name), timeout=self.config.timeout
                )

                title = result.title or ""

                fetch_result = FetchUrlResult(
                    url=url,
                    title=title,
                    content=result.text_content,
                )

                logger.info("successfully fetched and converted url: %s", url)

                return FetchUrlResponse(
                    query=url,
                    result=fetch_result,
                    error=None,
                )

        except asyncio.TimeoutError:
            logger.error("fetch_url timed out for %s after %d seconds", url, self.config.timeout)
            return FetchUrlResponse(
                query=url, result=None, error=f"conversion timed out after {self.config.timeout} seconds"
            )
        except httpx.HTTPError as e:
            logger.error("fetch_url http error for %s: %s", url, e)
            return FetchUrlResponse(query=url, result=None, error=f"http error: {str(e)}")
        except Exception as e:
            logger.error("fetch_url failed for %s: %s", url, e)
            return FetchUrlResponse(query=url, result=None, error=str(e))
