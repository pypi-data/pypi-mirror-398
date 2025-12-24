# Video Text Summarizer
[![PyPI version](https://badge.fury.io/py/video-text-summarizer.svg)](https://badge.fury.io/py/video-text-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/video-text-summarizer)](https://pepy.tech/project/video-text-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to analyze and summarize video content by processing pre-extracted textual information such as transcripts, subtitles, and descriptions. It leverages structured pattern matching to extract key topics, themes, and insights from lengthy videos, providing concise summaries without processing multimedia directly.

## 📌 Overview
This package helps users quickly grasp the essence of video content by summarizing textual data (transcripts, subtitles, etc.) using advanced language models. It is ideal for environments where only text data is available, enabling efficient content discovery and knowledge extraction.

---

## 📦 Installation

Install the package via pip:

```bash
pip install video_text_summarizer
```

---

## 🚀 Usage

### Basic Usage
```python
from video_text_summarizer import video_text_summarizer

# Summarize text using the default LLM7 model
response = video_text_summarizer(
    user_input="Your video transcript or text here..."
)
print(response)
```

### Custom LLM Usage
You can replace the default `ChatLLM7` with any other LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google Generative AI):

#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from video_text_summarizer import video_text_summarizer

llm = ChatOpenAI()
response = video_text_summarizer(
    user_input="Your video transcript or text here...",
    llm=llm
)
print(response)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from video_text_summarizer import video_text_summarizer

llm = ChatAnthropic()
response = video_text_summarizer(
    user_input="Your video transcript or text here...",
    llm=llm
)
print(response)
```

#### Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from video_text_summarizer import video_text_summarizer

llm = ChatGoogleGenerativeAI()
response = video_text_summarizer(
    user_input="Your video transcript or text here...",
    llm=llm
)
print(response)
```

---

## 🔧 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text (e.g., transcript, subtitles) to summarize. |
| `api_key` | `Optional[str]` | Your LLM7 API key (if not provided, falls back to `LLM7_API_KEY` environment variable). |
| `llm` | `Optional[BaseChatModel]` | A custom LangChain-compatible LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). If omitted, defaults to `ChatLLM7`. |

---

## 🔑 API Key & Rate Limits
- **Default LLM**: Uses `ChatLLM7` from [`langchain_llm7`](https://pypi.org/project/langchain-llm7/).
- **Free Tier**: Sufficient for most use cases (check [LLM7 docs](https://token.llm7.io/) for limits).
- **Custom API Key**: Pass via `api_key` parameter or set `LLM7_API_KEY` environment variable.
- **Get API Key**: Register at [LLM7 Token](https://token.llm7.io/) for free.

---

## 📝 License
MIT License (see [LICENSE](LICENSE) for details).

---

## 📢 Support & Issues
For bugs, feature requests, or support, open an issue on [GitHub](https://github.com/chigwell/video-text-summarizer/issues).

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)