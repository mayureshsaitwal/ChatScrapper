import asyncio
import re
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy
from utils import get_metadata_from_url
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

import shutil
import os
from pathlib import Path

filepath = "./data"
result_file = "./results.txt"


shutil.rmtree(filepath)
print("File Removed")
if os.path.isfile(result_file):
    os.remove(result_file)
    print("Result File Deleted")


filepath = Path("./data/metadata").mkdir(parents=True, exist_ok=True)
filepath = Path("./data/html").mkdir(parents=True, exist_ok=True)


url = "https://www.coeptech.ac.in/wp-sitemap-taxonomies-faculty_department-1.xml"
url2 = "https://www.coeptech.ac.in/"
# url = "https://docs.crawl4ai.com/"

sitemap = "sitemap.xml"

urlmain = url2 + sitemap


async def main():

    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=3,
            include_external=False,
            # max_pages=15,
            max_pages=10,
        ),
    )

    stop_urls = [".xml",".csv",".pdf"]

    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        results = await crawler.arun(url=urlmain, config=config)
        for result in results:
            with open(f"./result.txt", "a") as r:
                r.write("\n")
                r.write(result.url)

        for result in results:
            stop = 0
            for ext in stop_urls:
                if ext in result.url:
                    stop = 1
            # if stop_urls not in result.url:
            if not stop:
                metadata = get_metadata_from_url(result.url)
                # print(metadata)

                filename = result.url.replace(url2,'')
                last_word = re.search(r'[^/]+$', filename)
                if last_word:
                    last_word = last_word.group()
                    with open(f"./data/html/{last_word}.txt", "w+") as f:
                        f.write(result.markdown)
                    with open(f"./data/metadata/{last_word}.json", "w+") as file:
                        json.dump(metadata, file, indent=4)
                    with open(f"./data/links.txt","a") as link:
                        link.write("\n")
                        link.write(result.url)
                    # print(result.url)
        # Print the extracted content
        # print(result.markdown)

# Run the async main function
asyncio.run(main())
