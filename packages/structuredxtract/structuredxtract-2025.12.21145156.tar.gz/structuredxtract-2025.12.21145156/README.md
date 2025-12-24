# structuredxtract
[![PyPI version](https://badge.fury.io/py/structuredxtract.svg)](https://badge.fury.io/py/structuredxtract)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/structuredxtract)](https://pepy.tech/project/structuredxtract)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Extract structured information from unstructured text with pattern-matching precision.**

A Python package that simplifies structured data extraction from plain text inputs using a language model with pattern-matching capabilities. Ideal for surveys, feedback analysis, and report generation where consistent, well-formatted outputs are required.

---

## 🚀 Features
- **Pattern-based extraction**: Uses regex patterns to enforce structured output formats.
- **Flexible LLM integration**: Works with default `ChatLLM7` or any LangChain-compatible model.
- **No multimedia support**: Focuses solely on text-based inputs for reliability.
- **Consistent formatting**: Ensures responses match expected schemas (tables, summaries, key-value pairs).
- **Easy customization**: Replace default LLM with OpenAI, Anthropic, Google, or any other LangChain model.

---

## 📦 Installation

```bash
pip install structuredxtract
```

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from structuredxtract import structuredxtract

user_input = """
Name: John Doe
Age: 30
Occupation: Software Engineer
"""

response = structuredxtract(user_input)
print(response)  # Structured output based on predefined patterns
```

### Custom LLM Integration
Replace the default `ChatLLM7` with your preferred model:

#### OpenAI
```python
from langchain_openai import ChatOpenAI
from structuredxtract import structuredxtract

llm = ChatOpenAI()
response = structuredxtract(user_input, llm=llm)
```

#### Anthropic
```python
from langchain_anthropic import ChatAnthropic
from structuredxtract import structuredxtract

llm = ChatAnthropic()
response = structuredxtract(user_input, llm=llm)
```

#### Google Vertex AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from structuredxtract import structuredxtract

llm = ChatGoogleGenerativeAI()
response = structuredxtract(user_input, llm=llm)
```

---

## 🔑 API Key
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual override**: Pass via `api_key` parameter or set `LLM7_API_KEY` before importing.
  ```python
  import os
  os.environ["LLM7_API_KEY"] = "your_api_key_here"
  ```

Get a free API key at [LLM7 Token](https://token.llm7.io/).

---

## 📜 Parameters
| Parameter | Type       | Description                                                                 |
|-----------|------------|-----------------------------------------------------------------------------|
| `user_input` | `str`      | Plain text input to extract structured data from.                          |
| `api_key`   | `Optional[str]` | LLM7 API key (optional if using environment variable).                     |
| `llm`       | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). Defaults to `ChatLLM7`. |

---

## 📊 Output
Returns a `List[str]` of extracted data matching predefined patterns. Example:
```python
[
    {"Name": "John Doe", "Age": "30", "Occupation": "Software Engineer"},
    {"Key1": "Value1", "Key2": "Value2"}
]
```

---

## 🔄 Rate Limits
- **LLM7 Free Tier**: Sufficient for most use cases.
- **Custom API Key**: For higher limits, pass via `api_key` or environment variable.

---

## 📝 License
MIT

---

## 📢 Support & Issues
For bugs or feature requests, open an issue on [GitHub](https://github.com/chigwell/structuredxtract/issues).

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)