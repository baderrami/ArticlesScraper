import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import streamlit as st
import asyncio
from openai import OpenAI


# Function to crawl and get the fit markdown
async def get_fit_markdown(url: str):
    """
    Crawls the given URL and returns the fit markdown.

    Args:
        url (str): The article URL to crawl.

    Returns:
        dict: A dictionary containing success status, fit markdown, and length.
    """
    prune_filter = PruningContentFilter(
        threshold=0.45,
        threshold_type="dynamic",
        min_word_threshold=5
    )

    md_generator = DefaultMarkdownGenerator(content_filter=prune_filter)
    config = CrawlerRunConfig(markdown_generator=md_generator)

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


def send_messages_with_json_output(prompt, response_format):
    """
    Sends messages to the DeepSeek API with JSON response output enabled.

    Args:
        prompt (str): The user or system prompt to send.
        response_format: Format of the model's response, e.g., 'json_object'.

    Returns:
        dict: Parsed JSON response from the API.
    """
    # Include the system message for structured JSON instructions
    system_prompt = f"""
    You will receive an article in Markdown format. Translate the content into Arabic and structure the output as JSON.
    Ensure the JSON includes a "title", "content" (as a list of paragraphs), and a "metadata" section with the original article's word count.

    EXAMPLE OUTPUT JSON:
    {{
        "title": "Translated Title in Arabic",
        "content": [
            {{
                "type": "paragraph",
                "text": "Translated paragraph text in Arabic."
            }},
            ...
        ],
        "metadata": {{
            "original_word_count": 1234
        }}
    }}
    """

    # Messages to send
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # Call the API with JSON response format
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        response_format=response_format
    )
    return json.loads(response.choices[0].message.content)


# Streamlit UI
st.title("Markdown Extractor & Arabic Translator")

# Input field for URL
url = st.text_input("Enter the article URL:", "")

if st.button("Generate Markdown"):
    if url.strip():
        st.info("Processing your request... Please wait.")

        try:
            # Asynchronously crawl to retrieve the Markdown
            result = asyncio.run(get_fit_markdown(url))

            if result["success"]:
                st.success(f"Successfully extracted Markdown with {result['length']} characters!")
                st.text_area("Cleaned Markdown", result["fit_markdown"], height=300)

                # User prompt to trigger JSON generation
                user_prompt = "Please translate this Markdown content into Arabic and format it as JSON."

                # Enable JSON response format
                try:
                    json_response = send_messages_with_json_output(
                        prompt=result["fit_markdown"],
                        response_format={"type": "json_object"}
                    )
                    st.success("Markdown successfully translated and structured into JSON!")
                    st.text_area("Translated JSON:", json.dumps(json_response, indent=2), height=300)
                except Exception as e:
                    st.error(f"Failed to generate JSON output: {e}")

            else:
                st.error(f"Failed to extract markdown: {result['error_message']}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

    else:
        st.warning("Please enter a valid URL.")
