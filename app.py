import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import streamlit as st
import asyncio
from dataclasses import dataclass, asdict
from openai import OpenAI

# Initialize OpenAI client with DeepSeek setup
client = OpenAI(
    api_key="sk-74b5cb9a3e7f4b6396e97e264b9b9a4b",  # Replace with valid DeepSeek API key
    base_url="https://api.deepseek.com",
)


# Define the Article Data Transfer Object (DTO)
@dataclass
class Article:
    title: str
    content: str
    summary: str
    author: str
    date: str
    tags: str
    keywords: str
    language: str
    category: str


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
    Translate the provided Markdown content into Arabic and structure it into JSON with the following fields:
    - "title": Translated title of the article in Arabic.
    - "content": List of translated paragraphs, joined into a full text.
    - "summary": A brief summary of the article in Arabic.
    - "author": (Optional) The author of the article.
    - "date": (Optional) The publication date of the article.
    - "tags": A list of comma-separated topical tags in Arabic.
    - "keywords": A list of primary keywords (comma-separated) in Arabic.
    - "language": Set to 'Arabic'.
    - "category": Suggested category for the article.

    EXAMPLE OUTPUT:
    {
        "title": "عنوان المقال",
        "content": "هذا هو النص الكامل للمقال المترجم إلى اللغة العربية.",
        "summary": "ملخص المقال باللغة العربية.",
        "author": "اسم الكاتب (اختياري)",
        "date": "YYYY-MM-DD",
        "tags": "أمن, تحديثات, برمجيات",
        "keywords": "أدوبي, ثغرة, كولدفيون",
        "language": "Arabic",
        "category": "Technology"
    }
    """
    user_prompt = f"Content to process:\n{cleaned_markdown}"

    try:
        # Send request to OpenAI API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )

        # Extract token usage using dot notation
        token_usage = response.usage
        total_tokens = token_usage.total_tokens
        prompt_tokens = token_usage.prompt_tokens
        completion_tokens = token_usage.completion_tokens

        # Parse the JSON response content
        json_response = json.loads(response.choices[0].message.content)

        # Map the JSON response to the Article DTO
        article = Article(**json_response)

        return {
            "article": article,  # Parsed Article DTO
            "tokens_used": total_tokens,
            "tokens_prompt": prompt_tokens,
            "tokens_completion": completion_tokens,
        }

    except Exception as e:
        raise ValueError(f"Failed to process translation: {str(e)}")

# Streamlit UI
st.title(":newspaper: Article Translator & Editor")

# Input for Article URL
st.markdown("### :point_right: **Enter the Article URL**")
url = st.text_input("Article URL", placeholder="https://example.com/article")

if st.button("Process Markdown"):
    try:
        # Step 1: Extract and clean Markdown
        st.info("Step 1: Extracting article Markdown...")
        markdown_result = asyncio.run(get_fit_markdown(url))

        if markdown_result["success"]:
            word_count = markdown_result["length"]
            st.success(f"Markdown successfully extracted! Word count: {word_count}")

            # Step 2: Display Cleaned Markdown with Save Option
            cleaned_markdown = markdown_result["fit_markdown"]
            st.markdown("### :scroll: Cleaned Markdown")
            st.text_area("Cleaned Markdown", cleaned_markdown, height=150)

            # Step 3: Process Translation and Format into Article DTO
            st.info("Step 2: Translating and creating editable fields...")
            translation_result = process_translation_to_json(cleaned_markdown)
            article = translation_result["article"]  # Mapped to Article DTO
            tokens_used = translation_result["tokens_used"]

            # Step 4: Editable Fields for the Article DTO
            st.markdown("### :pencil: Editable Article Fields")
            title = st.text_input("Title (Arabic)", value=article.title)
            content = st.text_area("Content (Arabic)", value=article.content, height=200)
            summary = st.text_area("Summary (Arabic)", value=article.summary, height=100)
            author = st.text_input("Author", value=article.author)
            date = st.text_input("Date", value=article.date, placeholder="YYYY-MM-DD")
            tags = st.text_input("Tags (Comma-separated)", value=article.tags)
            keywords = st.text_input("Keywords (Comma-separated)", value=article.keywords)
            language = st.text_input("Language", value=article.language, disabled=True)  # Always Arabic
            category = st.text_input("Category", value=article.category)

            st.markdown("### :bar_chart: Token Usage Summary")
            st.write(f"- :heavy_check_mark: **Total Tokens Used**: {tokens_used}")
            st.write(f"- **Prompt Tokens**: {translation_result['tokens_prompt']}")
            st.write(f"- **Completion Tokens**: {translation_result['tokens_completion']}")

            # Button to Save Edited Data (Simulated Save)
            if st.button("Save Article"):
                updated_article = Article(
                    title=title,
                    content=content,
                    summary=summary,
                    author=author,
                    date=date,
                    tags=tags,
                    keywords=keywords,
                    language=language,
                    category=category,
                )
                st.success("Article updated successfully!")
                st.json(asdict(updated_article))  # Show updated article as JSON

        else:
            st.error(f"Failed to extract article: {markdown_result['error_message']}")

    except Exception as e:
        st.error(f"An error occurred: {e}")
