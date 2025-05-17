import os
import sys
import psutil
import asyncio
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy
import requests
from xml.etree import ElementTree

__location__ = os.path.dirname(os.path.abspath(__file__))
__output__ = os.path.join(__location__, "output")

# Append parent directory to system path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
file_path = "./"

from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def crawl_parallel(urls: List[str], max_concurrent: int = 3):
    print("\n Parallel Crawl\n")

    # Browser configuration for headless browsing
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,   # corrected from 'verbos=False'
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    # Crawler run configuration with DFS deep crawl strategy
    crawl_config = CrawlerRunConfig(
        DFSDeepCrawlStrategy(
            max_depth=3,
            include_external=False,
            max_pages=20
        ),
        cache_mode=CacheMode.BYPASS
    )

    # Initialize the asynchronous web crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        success_count = 0
        fail_count = 0

        # Process URLs in batches, controlling concurrent crawls
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i : i + max_concurrent]
            tasks = []

            for j, url in enumerate(batch):
                # Unique session ID per concurrent sub-task
                session_id = f"parallel_session_{i + j}"
                task = crawler.arun(url=url, config=crawl_config, session_id=session_id)
                tasks.append(task)

            # Gather the results of the batch of tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Evaluate the results of the crawl tasks
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    print(f"Error crawling {url}: {result}")
                    fail_count += 1
                elif result.success:
                    success_count += 1
                else:
                    fail_count += 1


        # for count,result in enumerate(results):
        #     with open(file_path/count.txt, 'w', encoding='utf-8') as f:
        #         f.write(result)


        # Print the summary of crawl results
        print(f"\nSummary:")
        print(f"  - Successfully crawled: {success_count}")
        print(f"  - Failed: {fail_count}")

    finally:
        # Ensure the crawler is properly closed after execution
        print("\nClosing crawler...")
        await crawler.close()
        print("Done")


def get_pydantic_ai_docs_urls():
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (https://ai.pydantic.dev/sitemap.xml) to get these URLs.

    Returns:
        List[str]: List of URLs
    """
    url = "https://www.coeptech.ac.in/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    sitemap_url = url + "sitemap.xml"
    try:
        response = requests.get(sitemap_url, headers=headers)
        response.raise_for_status()

        # Parse the XML
        root = ElementTree.fromstring(response.content)
        # print(root)

        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]

        print(urls)
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

async def main():
    urls = get_pydantic_ai_docs_urls()
    if urls:
        print(f"Found {len(urls)} URLs to crawl")
        # print(urls)
        await crawl_parallel(urls, max_concurrent=10)
    else:
        print("No URLs found to crawl")

if __name__ == "__main__":
    asyncio.run(main())
