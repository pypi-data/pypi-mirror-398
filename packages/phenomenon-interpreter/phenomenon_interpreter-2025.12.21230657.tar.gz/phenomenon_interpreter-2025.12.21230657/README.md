# phenomenon-interpreter
[![PyPI version](https://badge.fury.io/py/phenomenon-interpreter.svg)](https://badge.fury.io/py/phenomenon-interpreter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/phenomenon-interpreter)](https://pepy.tech/project/phenomenon-interpreter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for interpreting user-submitted text about natural or scientific phenomena, extracting structured insights, and classifying events based on textual input.

---

## 📌 Overview
`phenomenon_interpreter` is designed to analyze free-form descriptions of phenomena (e.g., solar storms, earthquakes, or other natural events) and generate structured summaries or classifications. It leverages large language models (LLMs) to extract domain-specific insights from unstructured text, enabling automated analysis without requiring multimedia processing.

---

## 🚀 Installation
Install the package via pip:

```bash
pip install phenomenon_interpreter
```

---

## 🔧 Usage

### Basic Usage (Default LLM: ChatLLM7)
```python
from phenomenon_interpreter import phenomenon_interpreter

user_input = "A massive solar storm caused radio blackouts in Australia today."
response = phenomenon_interpreter(user_input)
print(response)  # Structured output based on the input
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google Generative AI). Example:

#### Using OpenAI:
```python
from langchain_openai import ChatOpenAI
from phenomenon_interpreter import phenomenon_interpreter

llm = ChatOpenAI()
response = phenomenon_interpreter(user_input, llm=llm)
```

#### Using Anthropic:
```python
from langchain_anthropic import ChatAnthropic
from phenomenon_interpreter import phenomenon_interpreter

llm = ChatAnthropic()
response = phenomenon_interpreter(user_input, llm=llm)
```

#### Using Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from phenomenon_interpreter import phenomenon_interpreter

llm = ChatGoogleGenerativeAI()
response = phenomenon_interpreter(user_input, llm=llm)
```

---

## 🔑 API Key Configuration
By default, the package uses `ChatLLM7` with an API key fetched from the environment variable `LLM7_API_KEY`. You can:
1. Set it via environment variable:
   ```bash
   export LLM7_API_KEY="your_api_key_here"
   ```
2. Pass it directly:
   ```python
   from phenomenon_interpreter import phenomenon_interpreter
   response = phenomenon_interpreter(user_input, api_key="your_api_key_here")
   ```

Get a free API key from [LLM7](https://token.llm7.io/).

---

## 📝 Parameters
| Parameter | Type               | Description                                                                 |
|-----------|--------------------|-----------------------------------------------------------------------------|
| `user_input` | `str`             | The text describing the phenomenon to analyze.                             |
| `api_key`    | `Optional[str]`    | LLM7 API key (default: fetched from `LLM7_API_KEY` environment variable).   |
| `llm`         | `Optional[BaseChatModel]` | Custom LLM instance (e.g., `ChatOpenAI`, `ChatAnthropic`). Default: `ChatLLM7`. |

---

## 📊 Output
The function returns a **list of structured insights** extracted from the input text, formatted to match predefined patterns (e.g., impact classification, event nature).

---

## 🔄 Rate Limits
- **LLM7 Free Tier**: Sufficient for most use cases.
- **Custom API Key**: For higher rate limits, provide your own `api_key` or set `LLM7_API_KEY`.

---

## 📜 License
MIT License.

---

## 📢 Support & Issues
For bugs or feature requests, open an issue on [GitHub](https://github.com/chigwell/phenomenon-interpreter/issues).

---

## 👤 Author
- **Eugene Evstafev** ([GitHub](https://github.com/chigwell))
- **Email**: [hi@euegne.plus](mailto:hi@euegne.plus)

---