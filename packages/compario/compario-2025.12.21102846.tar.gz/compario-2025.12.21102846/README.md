# **Compario**
[![PyPI version](https://badge.fury.io/py/compario.svg)](https://badge.fury.io/py/compario)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/compario)](https://pepy.tech/project/compario)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Structured Text Similarity Comparison with Large Language Models**

Compario is a Python package that leverages **Normalized Compression Distance (NCD)** and **Large Language Models (LLMs)** to perform **structured similarity comparisons** between textual content. It analyzes user-provided text snippets, computes similarity scores, and returns formatted results—ideal for automated content comparison without processing raw documents directly.

---

## **🔧 Installation**

Install via pip:

```bash
pip install compario
```

---

## **🚀 Quick Start**

### **Basic Usage**
```python
from compario import compario

# Example: Compare two text snippets
user_input = """
Text 1: "The quick brown fox jumps over the lazy dog."
Text 2: "A fast brown fox leaps across the sleepy canine."
"""
response = compario(user_input)
print(response)
```

### **Custom LLM Integration**
By default, Compario uses **ChatLLM7** (from [`langchain_llm7`](https://pypi.org/project/langchain-llm7/)). You can override it with any LangChain-compatible LLM:

#### **Using OpenAI**
```python
from langchain_openai import ChatOpenAI
from compario import compario

llm = ChatOpenAI()
response = compario(user_input, llm=llm)
```

#### **Using Anthropic (Claude)**
```python
from langchain_anthropic import ChatAnthropic
from compario import compario

llm = ChatAnthropic()
response = compario(user_input, llm=llm)
```

#### **Using Google Generative AI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from compario import compario

llm = ChatGoogleGenerativeAI()
response = compario(user_input, llm=llm)
```

---

## **🔑 API Key & Rate Limits**
- **Default LLM (LLM7)**: Uses `LLM7_API_KEY` from environment variables or falls back to a default key.
- **Free Tier**: Sufficient for most use cases (check [LLM7 docs](https://token.llm7.io/) for limits).
- **Custom Key**: Pass via `api_key` parameter or set `LLM7_API_KEY` in your environment:
  ```python
  compario(user_input, api_key="your_api_key_here")
  ```
- **Get a Free Key**: [Register at LLM7](https://token.llm7.io/)

---

## **📝 Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text(s) to compare (e.g., multiple snippets separated by newlines). |
| `api_key` | `Optional[str]` | LLM7 API key (defaults to `LLM7_API_KEY` env var). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). |

---

## **📌 Key Features**
✅ **Pattern Matching + NCD**: Combines structured pattern analysis with compression-based similarity.
✅ **Flexible LLM Support**: Works with any LangChain-compatible model.
✅ **No Raw Document Processing**: Focuses on comparing extracted text snippets.
✅ **Clear Output**: Returns structured similarity results.

---

## **🐛 Issues & Support**
For bugs or feature requests, open an issue on **[GitHub](https://github.com/chigwell/compario/issues)**.

---

## **👤 Author**
- **Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
- **Email**: [hi@euegne.plus](mailto:hi@euegne.plus)

---