import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import streamlit as st
import asyncio
from openai import OpenAI

# Initialize OpenAI client with DeepSeek setup
client = OpenAI(
    api_key="sk-74b5cb9a3e7f4b6396e97e264b9b9a4b",  # Replace with valid DeepSeek API key
    base_url="https://api.deepseek.com",
)
tools = [
    {
        "type": "function",
        "function": {
            "name": "format_article",
            "description": (
                "Takes an article in Markdown format, translates it into Arabic, "
                "and structures it as JSON. This is useful for extracting article information and formatting."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Markdown content of the article."
                    }
                },
                "required": ["content"]
            }
        }
    }
]

async def get_fit_markdown(url: str):
    """
    Crawls the given URL and cleans the article Markdown.
    """
    prune_filter = PruningContentFilter(threshold=0.45, threshold_type="dynamic", min_word_threshold=5)
    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    config = CrawlerRunConfig(markdown_generator=md_generator)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if result.success:
            return {
                "success": True,
                "fit_markdown": result.markdown.fit_markdown.strip(),
                "length": len(result.markdown.fit_markdown.split())
            }
        return {"success": False, "error_message": result.error_message}


def process_translation_to_json(cleaned_markdown: str):
    """
    Send Markdown content for translation and JSON formatting.
    """
    system_prompt = """
    Translate Markdown content into Arabic and structure it into JSON with the following keys:
    - "title" in Arabic.
    - "content": List of paragraphs (translated).
    - "metadata": Word count.
    EXAMPLE OUTPUT:
    {
        "title": "عنوان المقال",
        "content": [{"type": "paragraph", "text": "فقرة مترجمة"}],
        "metadata": {"original_word_count": 10}
    }
    """
    user_prompt = f"Content to process:\n{cleaned_markdown}"

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise ValueError(f"Failed to process translation: {str(e)}")


# Streamlit UI
st.title("Markdown to Arabic JSON Translator")

url = st.text_input("Article URL:")
if st.button("Process Markdown"):
    try:
        markdown_result = asyncio.run(get_fit_markdown(url))
        if markdown_result["success"]:
            st.text_area("Cleaned Markdown:", markdown_result["fit_markdown"], height=200)

            translated_json = process_translation_to_json(markdown_result["fit_markdown"])
            st.text_area("Translated JSON:", json.dumps(translated_json, indent=2, ensure_ascii=False), height=300)
        else:
            st.error(f"Error extracting article: {markdown_result['error_message']}")
    except Exception as error:
        st.error(f"An error occurred: {error}")
