import asyncio
import os
import json
import base64
from pathlib import Path
from typing import List
from crawl4ai.proxy_strategy import ProxyConfig

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, CrawlResult
from crawl4ai import RoundRobinProxyStrategy
from crawl4ai import JsonCssExtractionStrategy, LLMExtractionStrategy
from crawl4ai import LLMConfig
from crawl4ai import PruningContentFilter, BM25ContentFilter
from crawl4ai import DefaultMarkdownGenerator
from crawl4ai import BFSDeepCrawlStrategy, DomainFilter, FilterChain
from crawl4ai import BrowserConfig


__cur_dir__ = Path(__file__).parent


async def demo_css_structured_extraction_no_schema():
    """Extract structured data using CSS selectors"""
    print("\n=== 5. CSS-Based Structured Extraction ===")
    # Sample HTML for schema generation (one-time cost)
    sample_html = """
<div class="body-post clear">
    <a class="story-link" href="https://thehackernews.com/2025/04/malicious-python-packages-on-pypi.html">
        <div class="clear home-post-box cf">
            <div class="home-img clear">
                <div class="img-ratio">
                    <img alt="..." src="...">
                </div>
            </div>
            <div class="clear home-right">
                <h2 class="home-title">Malicious Python Packages on PyPI Downloaded 39,000+ Times, Steal Sensitive Data</h2>
                <div class="item-label">
                    <span class="h-datetime"><i class="icon-font icon-calendar"></i>Apr 05, 2025</span>
                    <span class="h-tags">Malware / Supply Chain Attack</span>
                </div>
                <div class="home-desc"> Cybersecurity researchers have...</div>
            </div>
        </div>
    </a>
</div>
    """

    # Check if schema file exists and is not empty
    schema_file_path = f"{__cur_dir__}/tmp/schema.json"
    if os.path.exists(schema_file_path) and os.path.getsize(schema_file_path) > 0:
        with open(schema_file_path, "r") as f:
            try:
                schema = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading schema file: {e}")
                print("Regenerating schema...")
                schema = None
    else:
        schema = None

    # If schema is None, generate it
    if schema is None:
        # Generate schema using LLM (one-time setup)
        schema = JsonCssExtractionStrategy.generate_schema(
            html=sample_html,
            llm_config=LLMConfig(
                provider="deepseek/deepseek-chat",
                api_token="sk-74b5cb9a3e7f4b6396e97e264b9b9a4b",
            ),
            query="From https://thehackernews.com/, I have shared a sample of one news div with a title, date, and description. Please generate a schema for this news div.",
        )

        # Ensure the tmp directory exists
        Path(f"{__cur_dir__}/tmp").mkdir(parents=True, exist_ok=True)

        # Save the schema to a file
        with open(schema_file_path, "w") as f:
            json.dump(schema, f, indent=2)
            print(f"Schema saved to {schema_file_path}")

    # Create no-LLM extraction strategy with the generated schema
    extraction_strategy = JsonCssExtractionStrategy(schema)
    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    # Use the fast CSS extraction (no LLM calls during extraction)
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            "https://thehackernews.com", config=config
        )

        for result in results:
            print(f"URL: {result.url}")
            print(f"Success: {result.success}")
            if result.success:
                data = json.loads(result.extracted_content)
                print(json.dumps(data, indent=2))
            else:
                print("Failed to extract structured data")

async def main():
    """Run all demo functions sequentially"""
    print("=== Comprehensive Crawl4AI Demo ===")
    print("Note: Some examples require API keys or other configurations")

    # Run all demos
    # await demo_basic_crawl()
    # await demo_parallel_crawl()
    # await demo_fit_markdown()
    # await demo_llm_structured_extraction_no_schema()
    await demo_css_structured_extraction_no_schema()
    # await demo_deep_crawl()
    # await demo_js_interaction()
    # await demo_media_and_links()
    # await demo_screenshot_and_pdf()
    # # # await demo_proxy_rotation()
    # await demo_raw_html_and_file()

    # Clean up any temp files that may have been created
    print("\n=== Demo Complete ===")
    print("Check for any generated files (screenshots, PDFs) in the current directory")

if __name__ == "__main__":
    asyncio.run(main())
