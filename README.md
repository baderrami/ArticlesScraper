## **Project Documentation: Article Translator & Editor**

This document provides a comprehensive explanation of the **Article Translator & Editor** application, including the code functionality, architecture, how it works, and how to run the server efficiently. This application is a Streamlit-based server designed to fetch article content using web crawling, process it for translation into Arabic, and allow interactive editing before saving.

---

### **Overview**

The **Article Translator & Editor** enables users to:
1. Provide a URL of an article to fetch its content.
2. Extract and clean the article content using a web-crawling service.
3. Translate the cleaned content into Arabic.
4. Display the translated content for editing within a web interface.
5. Save the edited content in a structured JSON format.

The underlying services include:
- **Web Crawling**: Extract and clean content from the given article URL.
- **Markdown Processing**: Generate clean Markdown from the fetched content.
- **Translation Service**: Translates the article to Arabic using OpenAI's DeepSeek integration.

---

### **Project Architecture**

The project consists of three main components:
1. **Streamlit App (`app.py`)**:
    - Serves as the web UI for interacting with users.
    - Handles inputs (article URL) and displays intermediate results like cleaned Markdown, translated content, and token usage.

2. **Crawler Service**:
    - Manages the lifecycle of the `AsyncWebCrawler` instance, which fetches article content from the web.
    - Ensures proper initialization, reuse, and shutdown of the crawler instance to avoid resource conflicts.

3. **Translation Logic**:
    - Uses OpenAI's DeepSeek chat model to translate the cleaned Markdown into Arabic.
    - Structures the translated content into JSON fields:
        - Title
        - Author
        - Content
        - Summary
        - Tags
        - Keywords
        - Date
        - Language (Arabic)
        - Category

---

### **How It Works**

The application has the following workflow:

#### **1. Input the Article URL**
Users enter the URL of the article they'd like to process. This is done through a text input field provided on the Streamlit web interface.

#### **2. Fetch and Extract Content**
- The application uses the `CrawlerService` class to manage an instance of the `AsyncWebCrawler`, which:
    - Fetches the HTML content of the given URL.
    - Cleans the content using Markdown filters (e.g., removing unwanted HTML tags or noise).
- If the fetching and cleaning succeed, the cleaned Markdown is displayed on the app for review.

#### **3. Process Translation**
- The cleaned Markdown is sent to OpenAI's DeepSeek for translation into Arabic.
- The response returns structured JSON fields:
    - **Article Title:** Automatically translated into Arabic.
    - **Content:** Fully translated content in Arabic paragraphs.
    - **Summary:** A short translated summary of the article.
    - **Tags & Keywords:** Relevant topics and keywords extracted in Arabic.
    - **Date & Author:** Optional metadata.

#### **4. Editable Fields**
- The result of the translation process is rendered as editable fields in the Streamlit UI, enabling users to modify and refine the article's data, such as:
    - Title
    - Content
    - Summary
    - Tags
    - Keywords
    - Category, etc.

#### **5. Save and Output**
- Once finalized, users can save the updated article.
- The application displays the final article data in JSON format to allow exporting or external use.

---

### **Usage Instructions**

Follow these steps to set up and run the **Article Translator & Editor**:

#### **1. Install Required Packages**
Install the dependencies using `pip`. Required packages include:
- `streamlit` for the web interface.
- `crawl4ai` for advanced content web crawling.
- `openai` for text processing and translation services.

Run the following command in your terminal:
```shell script
pip install streamlit crawl4ai openai
```

#### **2. Start the Server**
Launch the Streamlit app by executing:
```shell script
streamlit run app.py
```

This command will start the local web server and open the application in your default browser.

Or create and run a docker container using the following commands
```shell script
   docker build -t streamlit-article-translator .
```

```shell script
   docker run -p 8501:8501 --env-file .env streamlit-article-translator
```

#### **3. Workflow: Using the Application**
1. Input the article URL.
2. Press the `Process Markdown` button to fetch, clean, and translate the article.
3. Edit the displayed fields (if required) to refine the title, summary, content, and other metadata.
4. Save the updated JSON structure:
    - The result will be displayed in a JSON format ready for external use.

---

### **Code Explanation**

#### **Key Components**

1. **`CrawlerService` Class**
    - Manages the lifecycle of the `AsyncWebCrawler`.
    - Provides methods to initialize (`start_crawler`), terminate (`stop_crawler`), and fetch content (`get_fit_markdown`) from the web.

   **Example Usage:**
```python
# Initialize CrawlerService globally
   crawler_service = CrawlerService()

   # Fetch content using the crawler
   markdown_result = asyncio.run(crawler_service.get_fit_markdown(article_url))
```

2. **`process_translation_to_json` Function**
    - Translates and structures the Markdown content sent to OpenAI DeepSeek API into JSON fields.

   **Input:** Cleaned Markdown  
   **Output:** Article structure in JSON format, including Arabic translations.

   **Example Usage:**
```python
article_translation = process_translation_to_json(cleaned_markdown)
   print(article_translation["article"])
```

3. **Streamlit User Interface**
    - Handles user input for the article URL.
    - Interacts with the backend to execute the workflow.
    - Displays intermediate and final results, including Markdown, translated article content, and token usage.

   **Important Sections:**
    - `st.text_input()`: Accepts the article URL from the user.
    - `st.text_area()`: Displays and allows editing of the translated content.
    - `st.json()`: Outputs the article as a structured JSON.

---

### **Key Features**

1. **Scalable Web Crawling**
    - Efficiently manages crawling sessions to prevent resource conflicts or browser closures using the `CrawlerService` class.

2. **Clean Markdown Generation**
    - Extracts the main content while removing unnecessary noise.

3. **OpenAI-Powered Translation**
    - Leverages DeepSeek for language translation and structured data extraction.

4. **Interactive UI**
    - Simple Streamlit frontend to process and edit articles seamlessly.

5. **JSON Export**
    - Outputs translated and updated articles, ready for saving or republishing.

---

### **Example Workflow**

**1. Start the server:**
```shell script
streamlit run app.py
```

**2. Open the browser and paste an article URL:**
Example: `https://example.com/article-to-translate`

**3. Process Markdown:**
- Fetches and cleans the content.
- Displays Markdown for initial review.

**4. Translate and Edit:**
- The article is processed and converted into editable JSON fields pre-filled with Arabic translations.

**5. Save the Result:**
- After editing, save the article to view its final JSON structure.

---

### **Advanced Details**

1. **Error Handling:**
    - Handles errors gracefully, such as URL fetch failures or translation timeouts.
    - Displays meaningful error messages to the user via `st.error`.

2. **Concurrency Management:**
    - Properly initializes and destroys the web-crawling instance for each session.
    - Ensures no leftover browser tabs or processes.

3. **Token Usage Summary:**
    - Tracks prompt and completion tokens to monitor API usage.

**Output Example:**
```json
{
    "title": "عنوان المقال",
    "content": "هذا هو النص الكامل للمقال باللغة العربية.",
    "summary": "ملخص المقال",
    "author": "اسم الكاتب",
    "date": "2023-11-01",
    "tags": "تقنية, برمجيات",
    "keywords": "API, ذكاء اصطناعي",
    "language": "Arabic",
    "category": "Technology"
}
```

---

### **Future Enhancements**
1. Add support for other languages.
2. Cache processed articles to enhance performance.
3. Provide file export options (e.g., `.json`, `.docx`).

This concludes the documentation for **Article Translator & Editor**.
