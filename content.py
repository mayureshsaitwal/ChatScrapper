import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

# url = "https://www.coeptech.ac.in/faculty/dr-khushal-d-khairnar/"
url = f"file://2.html"
async def main():
    config = CrawlerRunConfig(
        # Content thresholds
        # word_count_threshold=10,        # Minimum words per block

        # Tag exclusions
        excluded_tags=['form', 'header', 'footer', 'nav','a'],
        # target_elements=["main-content"],

        # Link filtering
        # exclude_external_links=True,
        # exclude_social_media_links=True,
        # Block entire domains
        # exclude_domains=["adtrackers.com", "spammynews.org"],
        # exclude_social_media_domains=["facebook.com", "twitter.com"],

        # Media filtering
        exclude_external_images=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url,
            config=config
        )
        # print("Partial HTML length:", len(result.cleaned_html))
        with open(f"./content3.txt", "w+") as file:
            file.write(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
