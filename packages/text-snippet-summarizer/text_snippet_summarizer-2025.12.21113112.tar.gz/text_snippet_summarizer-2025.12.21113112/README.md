# Text-Snippet-Summarizer
[![PyPI version](https://badge.fury.io/py/text-snippet-summarizer.svg)](https://badge.fury.io/py/text-snippet-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text-snippet-summarizer)](https://pepy.tech/project/text-snippet-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract structured, concise summaries from news headlines and brief texts using pattern matching and LLM interactions.**

This package helps researchers, journalists, and analysts quickly categorize and understand complex domain-specific issues (e.g., environmental crises, economic policies, geopolitics) by summarizing raw textual snippets. It avoids processing full documents, multimedia, or URLs, focusing on rapid, structured insights for decision-making or reporting.

---

## 🚀 Features
- **Pattern-based extraction** for structured summaries
- **LLM-powered summarization** with configurable models
- **Lightweight** – works with short text snippets
- **Flexible LLM integration** (supports OpenAI, Anthropic, Google, etc.)
- **Default LLM7 integration** (free tier sufficient for most use cases)

---

## 📦 Installation

```bash
pip install text_snippet_summarizer
```

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from text_snippet_summarizer import text_snippet_summarizer

user_input = "Climate change impacts: rising temperatures, extreme weather events, and biodiversity loss."
response = text_snippet_summarizer(user_input)
print(response)
```

### Custom LLM Integration
#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from text_snippet_summarizer import text_snippet_summarizer

llm = ChatOpenAI()
response = text_snippet_summarizer(user_input, llm=llm)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from text_snippet_summarizer import text_snippet_summarizer

llm = ChatAnthropic()
response = text_snippet_summarizer(user_input, llm=llm)
```

#### Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from text_snippet_summarizer import text_snippet_summarizer

llm = ChatGoogleGenerativeAI()
response = text_snippet_summarizer(user_input, llm=llm)
```

---

## 🔑 API Key Configuration
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual override**: Pass `api_key` directly:
  ```python
  response = text_snippet_summarizer(user_input, api_key="your_api_key_here")
  ```
- **Get a free LLM7 API key**: [Register here](https://token.llm7.io/)

---

## 📝 Function Signature
```python
text_snippet_summarizer(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]
```
- **`user_input`**: Raw text snippet to summarize.
- **`api_key`** (optional): LLM7 API key (defaults to `LLM7_API_KEY` env var).
- **`llm`** (optional): Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`).

---

## 📌 Notes
- **Rate Limits**: LLM7 free tier is sufficient for most use cases.
- **Output**: Returns a list of structured summary points matching predefined patterns.
- **Dependencies**: Uses `langchain_llm7` (default) or any `BaseChatModel` from LangChain.

---

## 📢 Issues & Support
Report bugs or feature requests:
🔗 [GitHub Issues](https://github.com/chigwell/text-snippet-summarizer/issues)

---

## 👤 Author
**Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
📧 [hi@euegne.plus](mailto:hi@euegne.plus)

---