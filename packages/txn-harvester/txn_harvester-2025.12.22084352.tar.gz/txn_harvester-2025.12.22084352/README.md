# txn-harvester
[![PyPI version](https://badge.fury.io/py/txn-harvester.svg)](https://badge.fury.io/py/txn-harvester)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/txn-harvester)](https://pepy.tech/project/txn-harvester)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract and structure financial transaction data from unstructured text**

`txn_harvester` is a Python package designed to parse and validate financial transaction data from raw text inputs (e.g., bank statements, transaction logs) into structured formats. It leverages **LLM7** (via `langchain_llm7`) by default, but supports any LangChain-compatible LLM for flexibility.

---

## 🚀 Features
- Extracts transaction details (amount, date, description, category) from unstructured text
- Validates output against predefined financial patterns using regex
- Supports custom LLMs (OpenAI, Anthropic, Google, etc.) via LangChain
- Lightweight and easy to integrate into financial workflows

---

## 📦 Installation

```bash
pip install txn_harvester
```

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from txn_harvester import txn_harvester

user_input = """
Paid for groceries at Whole Foods: $125.50 on 2024-05-15
Rent payment: $1500.00 (due 2024-05-20)
"""

response = txn_harvester(user_input)
print(response)
```

### Custom LLM (OpenAI Example)
```python
from langchain_openai import ChatOpenAI
from txn_harvester import txn_harvester

llm = ChatOpenAI(model="gpt-4")
response = txn_harvester(user_input, llm=llm)
```

### Custom LLM (Anthropic Example)
```python
from langchain_anthropic import ChatAnthropic
from txn_harvester import txn_harvester

llm = ChatAnthropic(model="claude-2")
response = txn_harvester(user_input, llm=llm)
```

### Custom LLM (Google Example)
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from txn_harvester import txn_harvester

llm = ChatGoogleGenerativeAI(model="gemini-pro")
response = txn_harvester(user_input, llm=llm)
```

---

## 🔑 API Key Configuration
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual**: Pass via `api_key` parameter or set `LLM7_API_KEY` in your shell:
  ```bash
  export LLM7_API_KEY="your_api_key_here"
  ```
- **Free Tier**: Sufficient for most use cases (rate limits apply).
- **Get Key**: Register at [https://token.llm7.io](https://token.llm7.io)

---

## 📝 Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Raw text containing financial transactions (required). |
| `api_key` | `Optional[str]` | LLM7 API key (optional; defaults to `LLM7_API_KEY`). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (optional; defaults to `ChatLLM7`). |

---

## 📝 Output
Returns a list of structured transaction data (e.g., `[{"amount": "$125.50", "date": "2024-05-15", ...}]`).

---

## 🔄 Customization
- Modify regex patterns in `prompts.py` to adapt to specific transaction formats.
- Extend the package by subclassing `txn_harvester` for domain-specific parsing.

---

## 📝 License
MIT

---

## 📧 Support & Issues
- **GitHub Issues**: [https://github.com/chigwell/txn-harvester/issues](https://github.com/chigwell/txn-harvester/issues)
- **Author**: Eugene Evstafev ([hi@euegne.plus](mailto:hi@euegne.plus))

---