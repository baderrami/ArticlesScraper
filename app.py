from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import streamlit as st
import asyncio


# Function to crawl and get the fit markdown
async def get_fit_markdown(url: str):
    """
    Crawls the given URL and returns the fit markdown.

    Args:
        url (str): The article URL to crawl.

    Returns:
        dict: A dictionary containing success status, fit markdown, and length.
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
            return {
                "success": True,
                "fit_markdown": result.markdown.fit_markdown,
                "length": len(result.markdown.fit_markdown)
            }
        else:
            return {
                "success": False,
                "error_message": result.error_message
            }


# Streamlit UI

st.title("Markdown Extractor")

# Input field for URL
url = st.text_input("Enter the article URL:", "")

# Button to trigger the markdown extraction
if st.button("Generate Markdown"):
    if url.strip():
        st.info("Processing your request... Please wait.")

        # Run the crawling process
        try:
            # Use asyncio to run the asynchronous function
            result = asyncio.run(get_fit_markdown(url))

            if result["success"]:
                # Display the fit markdown
                st.success(f"Successfully extracted markdown with {result['length']} characters!")
                st.text_area("Fit Markdown:", result["fit_markdown"], height=300)
            else:
                # Display the error message
                st.error(f"Failed to extract markdown: {result['error_message']}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
    else:
        st.warning("Please enter a valid URL.")
