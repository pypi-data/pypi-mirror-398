# DNS Insight Extractor
[![PyPI version](https://badge.fury.io/py/dns-insight-extractor.svg)](https://badge.fury.io/py/dns-insight-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/dns-insight-extractor)](https://pepy.tech/project/dns-insight-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for extracting structured insights from text-based content related to DNS blocking reports and network filtering incidents. This tool processes unstructured text to identify key information such as blocked domains, reasons for blocking, and contextual details (e.g., geographic or policy-related), enabling analysts to quickly derive actionable insights without manual parsing.

---

## 📦 Installation

Install the package via pip:

```bash
pip install dns_insight_extractor
```

---

## 🚀 Features

- Extracts structured data from DNS blocking reports and network filtering descriptions.
- Supports pattern matching and validation to ensure consistent output.
- Uses **LLM7** as the default language model (via `langchain_llm7`).
- Highly customizable—swap the default LLM for alternatives like OpenAI, Anthropic, or Google Generative AI.
- Environment-variable-friendly for API keys.

---

## 📝 Usage

### Basic Usage (Default LLM: LLM7)
```python
from dns_insight_extractor import dns_insight_extractor

# Example: Extract insights from a DNS blocking report
user_input = """
The following domains are blocked due to adult content:
- example.com
- porn-site.org
Reason: Policy violation (Section 3.2 of the network guidelines).
"""

response = dns_insight_extractor(user_input)
print(response)
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google Generative AI):

#### Using OpenAI:
```python
from langchain_openai import ChatOpenAI
from dns_insight_extractor import dns_insight_extractor

llm = ChatOpenAI()
response = dns_insight_extractor(user_input, llm=llm)
```

#### Using Anthropic:
```python
from langchain_anthropic import ChatAnthropic
from dns_insight_extractor import dns_insight_extractor

llm = ChatAnthropic()
response = dns_insight_extractor(user_input, llm=llm)
```

#### Using Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from dns_insight_extractor import dns_insight_extractor

llm = ChatGoogleGenerativeAI()
response = dns_insight_extractor(user_input, llm=llm)
```

---

## 🔧 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The unstructured text containing DNS blocking or filtering details. |
| `api_key` | `Optional[str]` | API key for LLM7 (default: fetched from `os.getenv("LLM7_API_KEY")`). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM instance (e.g., `ChatOpenAI`, `ChatAnthropic`). If omitted, defaults to `ChatLLM7`. |

---

## 🔑 API Key Setup

### Default (LLM7 Free Tier)
- The package uses LLM7 by default.
- Free tier rate limits are sufficient for most use cases.
- To use your own API key:
  ```bash
  export LLM7_API_KEY="your_api_key_here"
  ```
  Or pass it directly:
  ```python
  response = dns_insight_extractor(user_input, api_key="your_api_key")
  ```

### Get an LLM7 API Key
Sign up for free at: [https://token.llm7.io/](https://token.llm7.io/)

---

## 📚 Documentation & Support

- **GitHub Issues**: [https://github.com/chigwell/dns-insight-extractor/issues](https://github.com/chigwell/dns-insight-extractor/issues)
- **Author**: Eugene Evstafev ([@chigwell](https://github.com/chigwell))
- **Email**: [hi@euegne.plus](mailto:hi@euegne.plus)

---

## 🛠️ License
MIT License (see [LICENSE](https://github.com/chigwell/dns-insight-extractor/blob/main/LICENSE) for details).

---