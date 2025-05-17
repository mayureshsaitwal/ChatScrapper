import os
import asyncio
import json
from pydantic import BaseModel, Field
# from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from instruction import instruction

import os


# llm = "gemma3"
llm = "mistral"

if os.path.isfile(f"./{llm}.txt"):
    os.remove(f"./{llm}.txt")
    print("file removed")

class Product(BaseModel):
    content: str

async def main():
    llm_strategy = LLMExtractionStrategy(
        # llm_config = LLMConfig(provider="ollmama/llama3.2", base_url="http://localhost:11434"),
        llm_config = LLMConfig(provider=f"ollama/{llm}", base_url="http://localhost:11434"),
        # schema=Product.schema_json(), # Or use model_json_schema()
        schema=Product.model_json_schema(),
        extraction_type="schema",
        # instruction="Remove all the javascript and header and footer, only extract all the text content of the page under 'content'",
        # instruction=instruction,
        instruction="Extract all content under tags containing the word 'content' (e.g., div.content, section.content). Only return the text and exclude headers, footers, and any JavaScript.",
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="html",   # or "html", "fit_markdown"
        # extra_args={"temperature": 0.0, "max_tokens": 800}
    )

    # 2. Build the crawler config
    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS
    )

    # 3. Create a browser config if needed
    browser_cfg = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # 4. Let's say we want to crawl a single page
        result = await crawler.arun(
            url="https://www.coeptech.ac.in/about-us/about-university/",
            config=crawl_config
        )

        if result.success:
            # 5. The extracted content is presumably JSON
            data = json.loads(result.extracted_content)
            print(data)
            with open(f"./{llm}.txt", 'w') as file:
                for item in data:
                    if not item['error']:
                        file.write(item['content'] + "\n")
            print("Extracted items:", data)

            # 6. Show usage stats
            llm_strategy.show_usage()  # prints token usage
        else:
            print("Error:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
