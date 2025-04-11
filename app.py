from fastapi import FastAPI, Query, HTTPException
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

app = FastAPI()


@app.get("/get_fit_markdown/")
async def get_fit_markdown(url: str = Query(..., description="URL of the article to process")):
    """
    Endpoint that accepts a URL and returns the "fit markdown" for the article.

    Args:
        url (str): The article URL passed as a query parameter.

    Returns:
        Response containing the fit markdown or an error message.
    """
    # Step 1: Create a pruning filter
    prune_filter = PruningContentFilter(
        threshold=0.45,  # Lower → more content retained, higher → more content pruned
        threshold_type="dynamic",  # "fixed" or "dynamic"
        min_word_threshold=5  # Ignore nodes with <5 words
    )

    # Step 2: Insert the filter into a Markdown Generator
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)

    # Step 3: Create the crawler configuration
    config = CrawlerRunConfig(markdown_generator=md_generator)

    # Step 4: Start the crawling process
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

        if result.success:
            # Return the 'fit_markdown'
            return {
                "success": True,
                "fit_markdown": result.markdown.fit_markdown,
                "length": len(result.markdown.fit_markdown)
            }
        else:
            # Handle possible crawl errors
            raise HTTPException(status_code=400, detail=f"Error crawling the URL: {result.error_message}")


# Optional: Run the app with a custom asyncio loop configuration
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
