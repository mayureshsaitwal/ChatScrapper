import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

urls = ["https://www.coeptech.ac.in/wp-sitemap.xml"]

async def crawl_batch():
    browser_config = BrowserConfig(headless=True, verbose=False)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=False  # Default: get all results at once
    )

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Get all results at once
        results = await crawler.arun_many(
            urls=urls,
            config=run_config,
            dispatcher=dispatcher
        )

        # Process all results after completion
        for result in results:
            if result.success:
                await process_result(result)
            else:
                print(f"Failed to crawl {result.url}: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(crawl_batch())

