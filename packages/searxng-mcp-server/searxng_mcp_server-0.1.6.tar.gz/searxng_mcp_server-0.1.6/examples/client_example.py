#!/usr/bin/env python3
"""Example script demonstrating how to use SearxNGClient as a library."""

import asyncio

from searxng_mcp_server.config import Config
from searxng_mcp_server.tools import SearxNGClient
from searxng_mcp_server.log import get_logger

logger = get_logger(__name__)


async def example_web_search():
    """Example of performing a web search."""
    logger.info("starting web search example")

    # Create configuration from environment variables
    config = Config.from_env(None)

    # Initialize the client
    client = SearxNGClient(config)

    # Perform a web search
    response = await client.search_web(query="Python programming", language="en", max_results=5)

    if response.error:
        logger.error("web search failed: %s", response.error)
        return

    logger.info("found %d results for '%s'", response.total_results, response.query)

    for i, result in enumerate(response.results, 1):
        logger.info("result %d: %s", i, result.title)
        logger.info("  url: %s", result.url)
        logger.info("  engine: %s", result.engine)
        logger.info("  score: %s", result.score)
        if result.content:
            logger.info("  content: %s...", result.content[:100])
        if result.published_date:
            logger.info("  published_date: %s", result.published_date)
        logger.info("")


async def example_image_search():
    """Example of performing an image search."""
    logger.info("starting image search example")

    config = Config.from_env(None)
    client = SearxNGClient(config)

    response = await client.search_images(query="cute cats", max_results=3)

    if response.error:
        logger.error("image search failed: %s", response.error)
        return

    logger.info("found %d images for '%s'", response.total_results, response.query)

    for i, result in enumerate(response.results, 1):
        logger.info("image %d: %s", i, result.title)
        logger.info("  url: %s", result.url)
        logger.info("  engine: %s", result.engine)
        logger.info("  score: %s", result.score)
        if result.content:
            logger.info("  content: %s...", result.content[:100])
        if result.thumbnail_url:
            logger.info("  thumbnail_url: %s", result.thumbnail_url)
        if result.image_url:
            logger.info("  image_url: %s", result.image_url)
        if result.published_date:
            logger.info("  published_date: %s", result.published_date)
        logger.info("")


async def example_video_search():
    """Example of performing a video search."""
    logger.info("starting video search example")

    config = Config.from_env(None)
    client = SearxNGClient(config)

    response = await client.search_videos(query="machine learning tutorial", max_results=3)

    if response.error:
        logger.error("video search failed: %s", response.error)
        return

    logger.info("found %d videos for '%s'", response.total_results, response.query)

    for i, result in enumerate(response.results, 1):
        logger.info("video %d: %s", i, result.title)
        logger.info("  url: %s", result.url)
        logger.info("  engine: %s", result.engine)
        logger.info("  score: %s", result.score)
        if result.content:
            logger.info("  content: %s...", result.content[:100])
        if result.thumbnail_url:
            logger.info("  thumbnail_url: %s", result.thumbnail_url)
        if result.published_date:
            logger.info("  published_date: %s", result.published_date)
        logger.info("")


async def example_news_search():
    """Example of performing a news search."""
    logger.info("starting news search example")

    config = Config.from_env(None)
    client = SearxNGClient(config)

    response = await client.search_news(
        query="artificial intelligence",
        time_range="week",  # Recent news from the past week
        max_results=5,
    )

    if response.error:
        logger.error("news search failed: %s", response.error)
        return

    logger.info("found %d news articles for '%s'", response.total_results, response.query)

    for i, result in enumerate(response.results, 1):
        logger.info("article %d: %s", i, result.title)
        logger.info("  url: %s", result.url)
        logger.info("  engine: %s", result.engine)
        logger.info("  score: %s", result.score)
        logger.info("  source: %s", result.source)
        if result.content:
            logger.info("  content: %s...", result.content[:100])
        if result.published_date:
            logger.info("  published_date: %s", result.published_date)
        logger.info("")


async def example_advanced_search():
    """Example of advanced search with specific parameters."""
    logger.info("starting advanced search example")

    config = Config.from_env(None)
    client = SearxNGClient(config)

    # Search with advanced parameters
    response = await client.search_web(
        query="climate change",
        language="en-US",
        time_range="month",
        safesearch=True,
        max_results=3,
    )

    if response.error:
        logger.error("advanced search failed: %s", response.error)
        return

    logger.info("advanced search results for '%s'", response.query)

    for i, result in enumerate(response.results, 1):
        logger.info("result %d: %s", i, result.title)
        logger.info("  url: %s", result.url)
        logger.info("  engine: %s", result.engine)
        logger.info("  score: %s", result.score)
        if result.published_date:
            logger.info("  published: %s", result.published_date)
        logger.info("")


async def main():
    """Run all examples."""
    logger.info("starting searxng client library examples")
    logger.info("make sure to set SEARXNG_URL environment variable if you want to use a custom instance")
    logger.info("default: https://searx.be")

    try:
        await example_web_search()
        logger.info("=" * 50)

        await example_image_search()
        logger.info("=" * 50)

        await example_video_search()
        logger.info("=" * 50)

        await example_news_search()
        logger.info("=" * 50)

        await example_advanced_search()

    except Exception as e:
        logger.error("example failed: %s", e)
        logger.info("troubleshooting:")
        logger.info("1. check your internet connection")
        logger.info("2. verify SEARXNG_URL is accessible")
        logger.info("3. try a different SearxNG instance")


if __name__ == "__main__":
    asyncio.run(main())
