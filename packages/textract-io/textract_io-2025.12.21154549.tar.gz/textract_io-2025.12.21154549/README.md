# textract-io
[![PyPI version](https://badge.fury.io/py/textract-io.svg)](https://badge.fury.io/py/textract-io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/textract-io)](https://pepy.tech/project/textract-io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Structured Text Extraction for Scientific & Factual Data**

`textract_io` is a Python package designed to extract structured key information from scientific or factual text inputs. It leverages pattern matching and retry mechanisms to ensure accurate, reliable responses—ideal for generating summaries, extracting data, or categorizing text based on user prompts. Perfect for processing pre-extracted textual data from multimedia sources to produce concise, structured outputs for research, reporting, or database entry.

---

## 🚀 Features
- **Pattern-based extraction**: Uses regex patterns to enforce structured output.
- **LLM7 integration**: Defaults to `ChatLLM7` (from `langchain_llm7`) for extraction tasks.
- **Flexible LLM support**: Easily swap with any LangChain-compatible LLM (OpenAI, Anthropic, Google, etc.).
- **Error handling**: Robust retry logic and clear error messages.
- **Environment-aware**: Uses `LLM7_API_KEY` from environment variables or direct API key input.

---

## 📦 Installation

```bash
pip install textract_io
```

---

## 🔧 Usage

### Basic Usage (Default LLM7)
```python
from textract_io import textract_io

response = textract_io(user_input="Your text here...")
print(response)  # List of extracted data matching the pattern
```

### Custom LLM Integration
Replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google):

#### OpenAI Example
```python
from langchain_openai import ChatOpenAI
from textract_io import textract_io

llm = ChatOpenAI()
response = textract_io(user_input="Your text here...", llm=llm)
```

#### Anthropic Example
```python
from langchain_anthropic import ChatAnthropic
from textract_io import textract_io

llm = ChatAnthropic()
response = textract_io(user_input="Your text here...", llm=llm)
```

#### Google Generative AI Example
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from textract_io import textract_io

llm = ChatGoogleGenerativeAI()
response = textract_io(user_input="Your text here...", llm=llm)
```

---

## 🔑 API Key Configuration
- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual Override**: Pass the API key directly:
  ```python
  response = textract_io(user_input="Your text...", api_key="your_llm7_api_key")
  ```
- **Free API Key**: Register at [LLM7 Token](https://token.llm7.io/) to get started.

---

## 📝 Parameters
| Parameter | Type          | Description                                                                 |
|-----------|---------------|-----------------------------------------------------------------------------|
| `user_input` | `str`         | The input text to process.                                                  |
| `api_key`    | `Optional[str]`| LLM7 API key (defaults to `LLM7_API_KEY` environment variable).             |
| `llm`        | `Optional[BaseChatModel]` | Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). Defaults to `ChatLLM7`. |

---

## 📊 Rate Limits
- **LLM7 Free Tier**: Sufficient for most use cases.
- **Upgrade**: Use your own API key or environment variable for higher limits.

---

## 🔄 Error Handling
- If extraction fails, raises `RuntimeError` with a descriptive message.
- Retries internally to improve reliability.

---

## 📜 License
MIT License (see [LICENSE](https://github.com/chigwell/textract-io/blob/main/LICENSE)).

---

## 📢 Support & Issues
For bugs or feature requests, open an issue on [GitHub](https://github.com/chigwell/textract-io/issues).

---

## 👤 Author
**Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
📧 [hi@euegne.plus](mailto:hi@euegne.plus)

---