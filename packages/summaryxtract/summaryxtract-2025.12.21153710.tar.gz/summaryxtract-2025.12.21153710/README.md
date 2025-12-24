# **summaryxtract**
[![PyPI version](https://badge.fury.io/py/summaryxtract.svg)](https://badge.fury.io/py/summaryxtract)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/summaryxtract)](https://pepy.tech/project/summaryxtract)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for structured, reliable extraction of key insights from cultural texts using LLM-powered pattern matching.

---

## **Overview**
`summaryxtract` processes user-provided text (e.g., articles, discussions) to extract and summarize core themes, historical context, and contributions related to cultural topics. It leverages **LLM7** (by default) or custom LLMs (via LangChain) with retry mechanisms and pattern validation for consistent, accurate results.

### **Key Features**
✅ **Structured Summarization** – Extracts key insights from textual descriptions.
✅ **Pattern Matching & Validation** – Ensures responses adhere to predefined formats.
✅ **LLM Flexibility** – Works with **LLM7** (default) or any **LangChain-compatible LLM** (OpenAI, Anthropic, Google, etc.).
✅ **Retry Mechanism** – Handles API failures gracefully.
✅ **No Media Processing** – Focuses purely on text extraction.

---

## **Installation**
```bash
pip install summaryxtract
```

---

## **Usage**
### **Basic Usage (Default LLM7)**
```python
from summaryxtract import summaryxtract

response = summaryxtract(user_input="Your text about cultural history here...")
print(response)  # List of extracted insights
```

### **Custom LLM Integration**
You can replace the default **LLM7** with any **LangChain-compatible LLM** (e.g., OpenAI, Anthropic, Google).

#### **Example: Using OpenAI**
```python
from langchain_openai import ChatOpenAI
from summaryxtract import summaryxtract

llm = ChatOpenAI()
response = summaryxtract(user_input="Your text...", llm=llm)
```

#### **Example: Using Anthropic**
```python
from langchain_anthropic import ChatAnthropic
from summaryxtract import summaryxtract

llm = ChatAnthropic()
response = summaryxtract(user_input="Your text...", llm=llm)
```

#### **Example: Using Google Vertex AI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from summaryxtract import summaryxtract

llm = ChatGoogleGenerativeAI()
response = summaryxtract(user_input="Your text...", llm=llm)
```

---

## **Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The input text to analyze. |
| `api_key` | `Optional[str]` | **LLM7 API key** (if not provided, checks `LLM7_API_KEY` env var). |
| `llm` | `Optional[BaseChatModel]` | Custom **LangChain LLM** (optional; defaults to **LLM7**). |

---

## **Default LLM (LLM7)**
- **Provider:** [LLM7](https://token.llm7.io/) (free tier available).
- **Rate Limits:** Sufficient for most use cases (free tier).
- **Custom API Key:** Pass via `api_key` or `LLM7_API_KEY` env var.

**Get a Free API Key:**
🔗 [Register at LLM7](https://token.llm7.io/)

---

## **Error Handling**
- If the LLM call fails, a `RuntimeError` is raised with the error message.
- Retry mechanisms ensure robustness.

---

## **Contributing & Issues**
🐛 **Report bugs/feature requests:**
🔗 [GitHub Issues](https://github.com/chigwell/summaryxtract/issues)

---

## **Author**
👤 **Eugene Evstafev**
📧 **hi@euegne.plus**
🔗 [GitHub: chigwell](https://github.com/chigwell)

---