import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy
import streamlit as st
import asyncio
from dataclasses import dataclass, asdict
from openai import OpenAI
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import tiktoken
import os

# Load the environment variables from the .env file
load_dotenv()

# Retrieve the API key and Base URL from environment variables
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")

# Initialize OpenAI client with DeepSeek setup
client = OpenAI(
    api_key=api_key,
    base_url=base_url,
)

# Define token limit for splitting large content
TOKEN_LIMIT = 4000


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

def extract_main_content(html_content: str) -> str:
    """
    Extract main content from raw HTML using BeautifulSoup.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # Target <article> tag or main content-specific div
    article = soup.find("article") or soup.find("div", {"class": "article-body"})
    if article:
        return article.get_text(strip=True)
    return "No article content found."
def split_text_to_chunks(text: str, max_tokens: int = TOKEN_LIMIT) -> list:
    """
    Split long text into chunks based on token limits.
    """
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i: i + max_tokens]
        chunks.append(tokenizer.decode(chunk))
    return chunks
async def get_fit_markdown(url: str):
    """
    Crawls the given URL, extracts and cleans the article Markdown.
    """
    extraction_strategy = (
        LLMExtractionStrategy(
            llm_config=LLMConfig(
                provider="deepseek/deepseek-chat",
                api_token=api_key,
            ),
            instruction="""
    Extract only the main content of the article from the provided URL, keeping its structure, meaning, and key details. Do not include any unrelated or redundant information.
    **Include:**
    1. The main textual content of the article.
    2. Relevant headers, subheaders, and sections.
    3. The main featured image or any directly related visuals.
    4. Tabular data, lists, and quotes present within the article.
    
    **Exclude:**
    1. All raw HTML, inline styles, and metadata.
    2. Navigation elements, menus, and sidebars.
    3. Advertisements, cookie banners, or subscription prompts.
    4. Links to related articles, comments, or "follow us" sections.
    5. Boilerplate content like footers and disclaimers.
    
    **Formatting Rules:**
    1. Format the output as Markdown:
       - Use proper headers (`#`, `##`, `###`).
       - Format lists, tables, and code snippets as Markdown.
    2. Include the main featured image as a Markdown image link.
    3. Ensure the output is concise, well-structured, and free from unnecessary sections.
    
    The result should be a ready-to-use Markdown file representing only the article content, requiring no manual cleanup.
    """,
            chunk_token_threshold=4096,  # Adjust based on your needs
            verbose=True
        ))
    config = CrawlerRunConfig(extraction_strategy=extraction_strategy)

    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url, config=config)
            if result.success:
                # Process raw HTML
                raw_html = result.html
                clean_content = extract_main_content(raw_html)
                chunks = split_text_to_chunks(clean_content)
                return {
                    "success": True,
                    "fit_markdown": clean_content,
                    "chunks": chunks,
                    "length": len(clean_content.split())
                }
        return {"success": False, "error_message": result.error_message}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch content: {str(e)}")
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
    """
    user_prompt = f"Content to process:\n{cleaned_markdown}"

    try:
        # Send the content to deepseek again for translation and JSON formatting
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=1500,
        )

        # Extract token usage and handle JSON response
        response_json = json.loads(response.choices[0].message.content)

        article = Article(**response_json)

        return {
            "article": article,
            "tokens_used": response.usage.total_tokens,
            "tokens_prompt": response.usage.prompt_tokens,
            "tokens_completion": response.usage.completion_tokens,
        }
    except Exception as e:
        raise ValueError(f"Failed to process translation: {str(e)}")

async def main():
    # Streamlit UI
    st.title(":newspaper: Article Translator & Editor")

    # Input for Article URL
    st.markdown("### :point_right: **Enter the Article URL**")
    url = st.text_input("Article URL", placeholder="https://example.com/article")

    if st.button("Process Markdown"):
        try:
            st.info("Extracting and processing the article...")
            markdown_result = await get_fit_markdown(url)

            if markdown_result["success"]:
                st.success(f"Article Markdown extracted successfully! Word count: {markdown_result['length']}")
                cleaned_markdown = markdown_result["fit_markdown"]
                st.text_area("Cleaned Markdown", cleaned_markdown, height=200)

                chunks = markdown_result["chunks"]

                st.info("Translating and converting Markdown to JSON...")
                translation_result = process_translation_to_json(cleaned_markdown)
                article = translation_result["article"]  # Mapped to Article DTO
                tokens_used = translation_result["tokens_used"]

                # Display JSON output
                st.json(asdict(article))
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

                # Save Article Button
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
                st.error(f"Extraction failed: {markdown_result['error_message']}")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
