# schedule-llm-query

![PyPI version](https://img.shields.io/pypi/v/schedule-llm-query)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Downloads](https://img.shields.io/pypi/dm/schedule-llm-query)
![LinkedIn](https://img.shields.io/badge/LinkedIn-connect-blue)

A Python package for processing natural language queries about event schedules (e.g., FOSDEM 2026) and extracting structured information like session times, locations, and descriptions using an LLM.

---

## 📌 Overview
This package interprets user queries (e.g., *"What talks are on Sunday afternoon?"*) and extracts structured schedule data using pattern matching. The LLM is guided by a system prompt to format responses in a predefined structure, ensuring consistent and reliable output for applications.

---

## 🚀 Installation
```bash
pip install schedule-llm-query
```

---

## 🔧 Usage

### Basic Usage (Default LLM: ChatLLM7)
```python
from schedule_llm_query import schedule_llm_query

response = schedule_llm_query(
    user_input="What talks are on Sunday afternoon?",
    api_key="your_llm7_api_key"  # Optional (falls back to env var LLM7_API_KEY)
)
print(response)
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google).

#### Example: Using OpenAI
```python
from langchain_openai import ChatOpenAI
from schedule_llm_query import schedule_llm_query

llm = ChatOpenAI()
response = schedule_llm_query(
    user_input="Show me all Python talks on Saturday",
    llm=llm
)
print(response)
```

#### Example: Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from schedule_llm_query import schedule_llm_query

llm = ChatAnthropic()
response = schedule_llm_query(
    user_input="List all keynote sessions",
    llm=llm
)
print(response)
```

#### Example: Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from schedule_llm_query import schedule_llm_query

llm = ChatGoogleGenerativeAI()
response = schedule_llm_query(
    user_input="What are the talks at Hall 1?",
    llm=llm
)
print(response)
```

---

## 🔑 API Key
- **Default LLM**: Uses `ChatLLM7` (from [langchain_llm7](https://pypi.org/project/langchain-llm7/)).
- **Free Tier**: Sufficient for most use cases (rate limits apply).
- **Custom Key**: Pass via `api_key` parameter or `LLM7_API_KEY` environment variable.
  ```python
  schedule_llm_query(user_input="...", api_key="your_api_key")
  ```
- **Get a Key**: Register at [llm7.io](https://token.llm7.io/).

---

## 📝 Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The natural language query to process (e.g., *"What talks are on Sunday?"*). |
| `api_key` | `Optional[str]` | LLM7 API key (optional if using env var or custom LLM). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`). Falls back to `ChatLLM7` if `None`. |

---

## 🔄 Output Structure
The package returns structured data matching the regex pattern:
```json
[
  {
    "title": "Talk Title",
    "time": "14:00-15:30",
    "location": "Hall 2",
    "description": "Brief description..."
  }
]
```

---

## 📦 Dependencies
- `langchain-core` (for LLM integration)
- `langchain_llm7` (default LLM, optional for custom LLM)
- `llmatch` (for pattern extraction)

---

## 📜 License
MIT

---

## 📢 Support & Issues
For bugs/feature requests, open an issue on [GitHub](https://github.com/chigwell/schedule-llm-query/issues).

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [LinkedIn](https://linkedin.com/in/chigwell)

---