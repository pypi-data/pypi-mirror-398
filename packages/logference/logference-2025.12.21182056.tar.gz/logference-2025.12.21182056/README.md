# Logference
[![PyPI version](https://badge.fury.io/py/logference.svg)](https://badge.fury.io/py/logference)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/logference)](https://pepy.tech/project/logference)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract structured insights from logging system feedback using AI**

Logference is a Python package that analyzes user complaints or descriptions about logging systems, extracting structured insights such as common pain points, root causes, or improvement suggestions. It leverages an LLM to process input text and categorize feedback, helping teams quickly identify and address logging inefficiencies without manual review.

---

## 📦 Installation

Install the package via pip:

```bash
pip install logference
```

---

## 🚀 Usage

### Basic Usage (Default LLM: ChatLLM7)
```python
from logference import logference

user_input = """
The logs are too verbose and clutter the dashboard.
I can't filter logs by severity level efficiently.
The log rotation policy is causing performance issues.
"""

response = logference(user_input)
print(response)  # Structured feedback insights
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google Vertex AI):

#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from logference import logference

llm = ChatOpenAI()
response = logference(user_input, llm=llm)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from logference import logference

llm = ChatAnthropic()
response = logference(user_input, llm=llm)
```

#### Using Google Vertex AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from logference import logference

llm = ChatGoogleGenerativeAI()
response = logference(user_input, llm=llm)
```

---

## 🔧 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The raw text describing logging system feedback. |
| `api_key` | `Optional[str]` | Your LLM7 API key (if not using default). Falls back to `LLM7_API_KEY` env var. |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM instance (default: `ChatLLM7`). |

---

## 🔑 API Key
- **Default LLM**: Uses `ChatLLM7` from `langchain_llm7`.
- **Free Tier**: Sufficient for most use cases (rate limits apply).
- **Custom Key**: Pass via `api_key` or `LLM7_API_KEY` env var.
  ```python
  logference(user_input, api_key="your_api_key_here")
  ```
- **Get a Key**: Register at [LLM7 Token](https://token.llm7.io/).

---

## 📝 Features
- **Structured Output**: Extracts actionable insights from unstructured text.
- **Flexible LLM Support**: Works with any LangChain-compatible model.
- **Regex Validation**: Ensures output adheres to predefined patterns.

---

## 📋 Example Output
For input:
> *"Logs are slow to query, and the retention policy deletes critical data."*

Logference returns structured feedback like:
```python
[
    {"category": "Performance", "issue": "Slow log queries"},
    {"category": "Data Loss", "issue": "Retention policy deletes critical logs"}
]
```

---

## 📜 License
MIT

---

## 📢 Support & Issues
Report bugs or feature requests at:
[GitHub Issues](https://github.com/chigwell/logference/issues)

---

## 👤 Author
**Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
📧 [hi@euegne.plus](mailto:hi@euegne.plus)

---