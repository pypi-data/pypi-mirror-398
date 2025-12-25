# text2markdown-formatter
[![PyPI version](https://badge.fury.io/py/text2markdown-formatter.svg)](https://badge.fury.io/py/text2markdown-formatter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text2markdown-formatter)](https://pepy.tech/project/text2markdown-formatter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**text2markdown-formatter** is a lightweight Python package that converts unstructured raw text into clean, well‑structured Markdown documents. By leveraging the `llmatch-messages` utility and a default `ChatLLM7` model, the package ensures the output follows a consistent Markdown format, making it ideal for bloggers, writers, developers, and anyone who works with Markdown for documentation or content creation.

## Features

- Automatic transformation of notes, ideas, or drafts into polished Markdown.
- Built‑in support for the `ChatLLM7` model (no extra configuration required).
- Ability to plug in any LangChain‑compatible LLM (OpenAI, Anthropic, Google Gemini, etc.).
- Simple, single‑function API.

## Installation

```bash
pip install text2markdown_formatter
```

## Quick Start

```python
from text2markdown_formatter import text2markdown_formatter

raw_text = """
My project ideas:
- Build a web scraper.
- Write a blog post about AI.
- Create a small game.
"""

markdown = text2markdown_formatter(user_input=raw_text)
print("\n".join(markdown))
```

## API Reference

### `text2markdown_formatter(user_input: str, api_key: Optional[str] = None, llm: Optional[BaseChatModel] = None) -> List[str]`

| Parameter | Type | Description |
|-----------|------|-------------|
| **user_input** | `str` | The raw text you want to convert to Markdown. |
| **api_key** | `Optional[str]` | API key for the LLM7 service. If omitted, the function reads `LLM7_API_KEY` from the environment or defaults to `"None"` (which uses the free tier). |
| **llm** | `Optional[BaseChatModel]` | A LangChain LLM instance to use instead of the default `ChatLLM7`. You can pass any LangChain‑compatible chat model. |

The function returns a list of Markdown strings extracted from the LLM response.

## Using a Custom LLM

You can replace the default `ChatLLM7` with any LangChain chat model.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from text2markdown_formatter import text2markdown_formatter

my_llm = ChatOpenAI()
markdown = text2markdown_formatter(user_input="My notes...", llm=my_llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from text2markdown_formatter import text2markdown_formatter

my_llm = ChatAnthropic()
markdown = text2markdown_formatter(user_input="My notes...", llm=my_llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from text2markdown_formatter import text2markdown_formatter

my_llm = ChatGoogleGenerativeAI()
markdown = text2markdown_formatter(user_input="My notes...", llm=my_llm)
```

## Environment Variables

- `LLM7_API_KEY` – Your API key for the LLM7 service. Obtain a free key by registering at https://token.llm7.io/.

If you don’t set this variable, the package will fall back to the free tier limits of LLM7.

## Rate Limits

The free tier of LLM7 provides sufficient quota for typical usage of this package. If you need higher limits, supply your own API key via `api_key` argument or the `LLM7_API_KEY` environment variable.

## Contributing & Support

- **Issues:** <https://github.com/chigwell/text2markdown-formatter/issues>
- **Pull Requests:** Contributions are welcome! Please follow the standard GitHub workflow.

## Author

**Eugene Evstafev** – hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)

---

Enjoy turning raw text into beautiful Markdown with **text2markdown-formatter**!