# devide-spec
[![PyPI version](https://badge.fury.io/py/devide-spec.svg)](https://badge.fury.io/py/devide-spec)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/devide-spec)](https://pepy.tech/project/devide-spec)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Transform unstructured developer tool ideas into structured, actionable product specifications.**

`devide_spec` is a Python package that converts natural language descriptions of developer tools into structured, well-defined specifications. It extracts key features, target users, and potential challenges, providing a clear roadmap for development.

---

## 🚀 Features
- Extracts structured specifications from unstructured text inputs
- Supports customizable LLM backends (LLM7 by default)
- Configurable via environment variables or direct API key input
- Works seamlessly with popular LangChain LLM integrations

---

## 📦 Installation

```bash
pip install devide_spec
```

---

## 🔧 Usage

### Basic Usage (with default LLM7)
```python
from devide_spec import devide_spec

response = devide_spec(user_input="I want a CLI tool that helps developers manage their Docker containers with a simple command interface")
print(response)
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM:

#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from devide_spec import devide_spec

llm = ChatOpenAI()
response = devide_spec(user_input="My tool idea...", llm=llm)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from devide_spec import devide_spec

llm = ChatAnthropic()
response = devide_spec(user_input="My tool idea...", llm=llm)
```

#### Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from devide_spec import devide_spec

llm = ChatGoogleGenerativeAI()
response = devide_spec(user_input="My tool idea...", llm=llm)
```

---

## 🔑 API Key Configuration
The package uses **LLM7** by default. You can:
1. Set your API key via environment variable:
   ```bash
   export LLM7_API_KEY="your_api_key_here"
   ```
2. Or pass it directly:
   ```python
   from devide_spec import devide_spec
   response = devide_spec(user_input="My tool idea...", api_key="your_api_key_here")
   ```

Get a free LLM7 API key at [https://token.llm7.io/](https://token.llm7.io/).

---

## 📝 Input Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The natural language description of your tool idea |
| `api_key` | `Optional[str]` | LLM7 API key (optional if using environment variable) |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (optional, defaults to `ChatLLM7`) |

---

## 📌 Output
The function returns a **list of structured specifications** extracted from the input text, formatted to match a predefined regex pattern.

---

## 🔄 Rate Limits
- **LLM7 Free Tier** is sufficient for most use cases.
- For higher rate limits, use your own API key or upgrade your LLM7 plan.

---

## 📖 License
MIT

---

## 📧 Support & Issues
For bugs, feature requests, or support, please open an issue at:
[https://github.com/chigwell/devide-spec/issues](https://github.com/chigwell/devide-spec/issues)

---

## 👤 Author
**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [GitHub: chigwell](https://github.com/chigwell)

---