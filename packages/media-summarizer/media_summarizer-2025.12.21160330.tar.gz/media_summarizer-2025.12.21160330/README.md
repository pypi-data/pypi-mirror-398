# media-summarizer
[![PyPI version](https://badge.fury.io/py/media-summarizer.svg)](https://badge.fury.io/py/media-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/media-summarizer)](https://pepy.tech/project/media-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package that interprets and summarizes user‑provided textual descriptions of multimedia content (e.g., video or audio transcripts). It turns raw or pre‑processed text extracts into structured overviews or key‑point lists, making content analysis, cataloguing, and review straightforward—without handling the media files themselves.

---

## Installation

```bash
pip install media_summarizer
```

---

## Quick Start

```python
from media_summarizer import media_summarizer

# Example raw transcript or description
user_input = """
In this video the presenter explains the difference between supervised and unsupervised learning,
covers examples of classification, regression, clustering, and ends with a short Q&A.
"""

# Call the summarizer with default LLM (ChatLLM7)
summary = media_summarizer(user_input)

print(summary)
# -> ['The video covers supervised vs unsupervised learning', 
#     'Examples: classification, regression, clustering', 
#     'Ends with a short Q&A']
```

---

## Parameters

| Name      | Type                     | Description |
|-----------|--------------------------|-------------|
| `user_input` | `str` | Textual content (e.g., transcript, description) to be summarized. |
| `llm` (optional) | `BaseChatModel` | A LangChain chat model instance. If omitted, the package creates a `ChatLLM7` instance automatically. |
| `api_key` (optional) | `str` | API key for `ChatLLM7`. If omitted, the function reads the `LLM7_API_KEY` environment variable, and if that is missing it falls back to `"None"` (the default free‑tier key). |

---

## Using a Custom LLM

You can pass any LangChain‑compatible chat model instead of the default `ChatLLM7`.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from media_summarizer import media_summarizer

llm = ChatOpenAI(model="gpt-4o-mini")
summary = media_summarizer(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from media_summarizer import media_summarizer

llm = ChatAnthropic(model="claude-3-sonnet-20240229")
summary = media_summarizer(user_input, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from media_summarizer import media_summarizer

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
summary = media_summarizer(user_input, llm=llm)
```

---

## API Key & Rate Limits

- **Default LLM**: `ChatLLM7` from the `langchain_llm7` package ([PyPI link](https://pypi.org/project/langchain-llm7/)).  
- **Free Tier**: The default rate limits of the LLM7 free tier are sufficient for most use cases of this package.  
- **Higher Limits**: Provide your own API key via the `LLM7_API_KEY` environment variable or directly:

```python
summary = media_summarizer(user_input, api_key="your_personal_api_key")
```

- **Get a free API key**: Register at <https://token.llm7.io/>.

---

## License

Distributed under the MIT License. See the `LICENSE` file for details.

---

## Contributing & Support

- **Issues & feature requests**: <https://github.com/chigwell/media-summarizer/issues>
- **Author**: Eugene Evstafev – <hi@eugene.plus>
- **GitHub**: <https://github.com/chigwell>

Feel free to open issues, submit pull requests, or contact the author for any questions.