# VintageConsoleInfo
[![PyPI version](https://badge.fury.io/py/vintageconsoleinfo.svg)](https://badge.fury.io/py/vintageconsoleinfo)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vintageconsoleinfo)](https://pepy.tech/project/vintageconsoleinfo)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for extracting structured information about vintage gaming consoles from unstructured user input. Ideal for collectors, enthusiasts, and restorers who need quick access to key details like hardware specs, game libraries, and historical context.

---

## 📦 Installation

Install the package via pip:

```bash
pip install vintageconsoleinfo
```

---

## 🚀 Features

- Extracts structured data from textual descriptions of vintage consoles (e.g., Interton Video Computer 4000).
- Supports customizable LLM backends (default: **LLM7**).
- Uses regex pattern matching for reliable data extraction.
- Works with OpenAI, Anthropic, Google, or any LangChain-compatible LLM.

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from vintageconsoleinfo import vintageconsoleinfo

# Example input about the Interton Video Computer 4000
user_input = """
The Interton Video Computer 4000 is a 1983 console with a Z80 CPU,
4KB RAM, and a built-in keyboard. It supports games like 'Space Invaders'
and 'Breakout'.
"""

response = vintageconsoleinfo(user_input)
print(response)  # Structured output (e.g., specs, games, etc.)
```

### Custom LLM (e.g., OpenAI)
```python
from langchain_openai import ChatOpenAI
from vintageconsoleinfo import vintageconsoleinfo

llm = ChatOpenAI(model="gpt-3.5-turbo")
response = vintageconsoleinfo(user_input, llm=llm)
```

### Custom LLM (e.g., Anthropic)
```python
from langchain_anthropic import ChatAnthropic
from vintageconsoleinfo import vintageconsoleinfo

llm = ChatAnthropic(model="claude-2")
response = vintageconsoleinfo(user_input, llm=llm)
```

### Custom LLM (e.g., Google)
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vintageconsoleinfo import vintageconsoleinfo

llm = ChatGoogleGenerativeAI(model="gemini-pro")
response = vintageconsoleinfo(user_input, llm=llm)
```

---

## 🔑 API Key Configuration

### Default (LLM7)
- Uses `LLM7_API_KEY` from environment variables or falls back to a default.
- Free tier rate limits are sufficient for most use cases.
- Get a free API key: [LLM7 Registration](https://token.llm7.io/).

### Override API Key
```python
response = vintageconsoleinfo(user_input, api_key="your_llm7_api_key")
```

---

## 📌 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Text describing a vintage console (required). |
| `api_key` | `Optional[str]` | LLM7 API key (optional; defaults to env var). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (optional; defaults to `ChatLLM7`). |

---

## 📝 Notes

- The package uses **LLM7** by default (via `langchain_llm7`).
- For production use, ensure your LLM backend meets rate limits.
- Extracted data follows a structured format (regex-based).

---

## 📜 License
MIT

---

## 📧 Support & Issues
Report bugs or request features at:
🔗 [GitHub Issues](https://github.com/chigwell/vintageconsoleinfo/issues)

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)

---