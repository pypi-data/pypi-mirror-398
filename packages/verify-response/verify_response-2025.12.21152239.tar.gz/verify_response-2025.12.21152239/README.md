# verify_response
[![PyPI version](https://badge.fury.io/py/verify-response.svg)](https://badge.fury.io/py/verify-response)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/verify-response)](https://pepy.tech/project/verify-response)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that ensures structured, verified, and reliable responses from language models by enforcing strict output formatting and confidence indicators. This package helps reduce ambiguity and overconfidence in AI-generated outputs, making it ideal for applications requiring precise data extraction, summaries, or structured insights.

---

## 📦 Installation

Install the package via pip:

```bash
pip install verify_response
```

---

## 🚀 Features

- **Structured Outputs**: Enforces strict regex-based response formatting to ensure consistency.
- **Confidence Indicators**: Provides clear indicators of response reliability.
- **Flexible LLM Support**: Works with default `ChatLLM7` or any LangChain-compatible LLM.
- **No Multimedia Processing**: Focuses solely on text inputs and structured outputs.
- **Transparency**: Reduces false confidence by validating output against predefined patterns.

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from verify_response import verify_response

response = verify_response(user_input="What is the capital of France?")
print(response)  # Structured, verified output
```

### Custom LLM (OpenAI)
```python
from langchain_openai import ChatOpenAI
from verify_response import verify_response

llm = ChatOpenAI()
response = verify_response(user_input="Summarize this text...", llm=llm)
print(response)
```

### Custom LLM (Anthropic)
```python
from langchain_anthropic import ChatAnthropic
from verify_response import verify_response

llm = ChatAnthropic()
response = verify_response(user_input="Extract key points...", llm=llm)
print(response)
```

### Custom LLM (Google Generative AI)
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from verify_response import verify_response

llm = ChatGoogleGenerativeAI()
response = verify_response(user_input="Analyze this data...", llm=llm)
print(response)
```

---

## 🔑 API Key Configuration

### Default (LLM7 Free Tier)
The package defaults to `ChatLLM7` with the API key loaded from the environment variable `LLM7_API_KEY`. If not set, it falls back to a default key (not recommended for production).

### Custom API Key
Pass your API key directly or via environment variable:
```python
# Directly
verify_response(user_input="...", api_key="your_llm7_api_key")

# Via environment variable
export LLM7_API_KEY="your_llm7_api_key"
verify_response(user_input="...")
```

**Get a free API key**: [LLM7 Token Registration](https://token.llm7.io/)

---

## 📝 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The input text to process. |
| `api_key` | `Optional[str]` | LLM7 API key (defaults to `LLM7_API_KEY` env var). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). Defaults to `ChatLLM7`. |

---

## 📊 Rate Limits
The default `ChatLLM7` free tier supports most use cases. For higher limits, use your own API key or upgrade via [LLM7](https://token.llm7.io/).

---

## 📜 License
MIT

---

## 📢 Support & Issues
For bugs or feature requests, open an issue on [GitHub](https://github.com/chigwell/verify-response/issues).

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)

---