# iac-summarizer
[![PyPI version](https://badge.fury.io/py/iac-summarizer.svg)](https://badge.fury.io/py/iac-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/iac-summarizer)](https://pepy.tech/project/iac-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract structured summaries from infrastructure-as-code (IaC) discussions**

A Python package that analyzes technical arguments in text discussions about IaC practices and extracts concise, structured summaries. Ideal for developers and architects who need quick insights from lengthy technical debates, forum posts, or documentation.

---

## 🚀 Features
- Extracts core arguments from text discussions about IaC (e.g., Terraform, CloudFormation, Pulumi).
- Validates output against predefined patterns for consistency.
- Supports custom LLMs via LangChain for flexibility.
- Defaults to **ChatLLM7** (from [langchain_llm7](https://pypi.org/project/langchain-llm7/)) for simplicity.

---

## 📦 Installation

```bash
pip install iac_summarizer
```

---

## 🔧 Usage

### Basic Usage (Default LLM: ChatLLM7)
```python
from iac_summarizer import iac_summarizer

user_input = """
Discussion about drawbacks of generic multi-cloud Terraform modules:
'These modules lack specificity, leading to bloated configurations and harder maintenance...'
"""

response = iac_summarizer(user_input)
print(response)
```

### Custom LLM (e.g., OpenAI, Anthropic, Google)
Replace the default LLM with your preferred provider:

#### OpenAI
```python
from langchain_openai import ChatOpenAI
from iac_summarizer import iac_summarizer

llm = ChatOpenAI()
response = iac_summarizer(user_input, llm=llm)
```

#### Anthropic
```python
from langchain_anthropic import ChatAnthropic
from iac_summarizer import iac_summarizer

llm = ChatAnthropic()
response = iac_summarizer(user_input, llm=llm)
```

#### Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from iac_summarizer import iac_summarizer

llm = ChatGoogleGenerativeAI()
response = iac_summarizer(user_input, llm=llm)
```

---

## 🔑 API Key Configuration
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Override**: Pass directly via `api_key` parameter:
  ```python
  response = iac_summarizer(user_input, api_key="your_llm7_api_key")
  ```
- **Get a Free Key**: Register at [https://token.llm7.io/](https://token.llm7.io/).

---

## 📌 Parameters
| Parameter | Type          | Description                                                                 |
|-----------|---------------|-----------------------------------------------------------------------------|
| `user_input` | `str`         | Text to analyze (e.g., forum posts, articles, or comments).                |
| `llm`       | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). Defaults to `ChatLLM7`. |
| `api_key`   | `Optional[str]` | LLM7 API key (falls back to `LLM7_API_KEY` env var).                       |

---

## 📝 Output Format
The function returns a **list of structured summaries** extracted from the input text, validated against predefined patterns.

---

## 🔄 Rate Limits
- **Default (LLM7 Free Tier)**: Sufficient for most use cases.
- **Upgrade**: Use your own API key or environment variable (`LLM7_API_KEY`).

---

## 📖 License
MIT

---

## 📢 Support & Issues
For bugs or feature requests, open an issue at:
[https://github.com/chigwell/iac-summarizer/issues](https://github.com/chigwell/iac-summarizer/issues)

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)