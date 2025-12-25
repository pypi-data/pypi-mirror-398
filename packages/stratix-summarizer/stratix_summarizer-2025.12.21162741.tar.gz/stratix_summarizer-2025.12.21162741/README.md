# Stratix-Summarizer
[![PyPI version](https://badge.fury.io/py/stratix-summarizer.svg)](https://badge.fury.io/py/stratix-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/stratix-summarizer)](https://pepy.tech/project/stratix-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract structured insights from startup funding narratives**

Stratix-Summarizer is a Python package designed to analyze and summarize business strategy narratives, investor communications, crowdfunding campaign descriptions, or any startup-related text. It extracts structured insights about funding activities—such as **fundraising amounts, sources, and strategic context**—from unstructured text, providing clear, actionable summaries for investors, entrepreneurs, and analysts.

---

## 🚀 Features
- **Structured Extraction**: Parses unstructured text to extract key funding-related details.
- **Flexible LLM Integration**: Works with **LLM7 (default)**, OpenAI, Anthropic, Google, or any LangChain-compatible LLM.
- **Regex Validation**: Ensures extracted data matches predefined patterns for consistency.
- **Lightweight & Fast**: Optimized for quick processing of startup funding narratives.

---

## 📦 Installation

Install via pip:

```bash
pip install stratix_summarizer
```

---

## 🔧 Usage Examples

### **Basic Usage (Default LLM7)**
```python
from stratix_summarizer import stratix_summarizer

user_input = """
Our startup raised $5M in Series A funding from Sequoia Capital and a16z.
The funds will be used for R&D and scaling our AI product.
"""

response = stratix_summarizer(user_input)
print(response)
```

### **Custom LLM Integration**
#### **Using OpenAI**
```python
from langchain_openai import ChatOpenAI
from stratix_summarizer import stratix_summarizer

llm = ChatOpenAI()
response = stratix_summarizer(user_input, llm=llm)
```

#### **Using Anthropic**
```python
from langchain_anthropic import ChatAnthropic
from stratix_summarizer import stratix_summarizer

llm = ChatAnthropic()
response = stratix_summarizer(user_input, llm=llm)
```

#### **Using Google Vertex AI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from stratix_summarizer import stratix_summarizer

llm = ChatGoogleGenerativeAI()
response = stratix_summarizer(user_input, llm=llm)
```

---

## 🔑 API Key Configuration
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual Override**: Pass the API key directly:
  ```python
  stratix_summarizer(user_input, api_key="your_llm7_api_key")
  ```
- **Get a Free API Key**: [Register at LLM7](https://token.llm7.io/)

---

## 📝 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text to analyze (e.g., funding narratives, investor updates). |
| `api_key` | `Optional[str]` | LLM7 API key (if not using default). |
| `llm` | `Optional[BaseChatModel]` | Custom LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). |

---

## 📊 Output
Returns a **list of structured insights** (e.g., extracted funding amounts, sources, and strategic notes) in a machine-readable format.

---

## 🔄 Rate Limits
- **LLM7 Free Tier**: Sufficient for most use cases.
- **Upgrade**: Pass a custom API key for higher limits.

---

## 📜 License
MIT

---

## 📢 Support & Issues
For bugs or feature requests, open an issue:
🔗 [GitHub Issues](https://github.com/chigwell/stratix-summarizer/issues)

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🐙 [GitHub: chigwell](https://github.com/chigwell)