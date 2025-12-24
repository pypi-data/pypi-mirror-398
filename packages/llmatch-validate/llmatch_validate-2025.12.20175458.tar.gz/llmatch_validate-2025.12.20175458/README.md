# llmatch-validate

![PyPI version](https://img.shields.io/pypi/v/llmatch-validate)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Downloads](https://img.shields.io/pypi/dm/llmatch-validate)
![LinkedIn](https://img.shields.io/badge/LinkedIn-connect-blue)

A Python package for processing and validating user inputs using advanced language models, ensuring structured and consistent responses. Built on top of `llmatch-messages`, this package extracts and validates key information from text inputs, making it ideal for applications requiring structured data extraction, format validation, or response consistency.

---

## 📦 Installation

Install the package via pip:

```bash
pip install llmatch-validate
```

---

## 🚀 Features

- **Structured Data Extraction**: Extracts key information from unstructured text inputs.
- **Regex Validation**: Ensures extracted data matches predefined patterns.
- **Flexible LLM Integration**: Works with default `ChatLLM7` or any LangChain-compatible LLM.
- **Error Handling & Diagnostics**: Provides clear error messages for failed validations.
- **Retry Mechanism**: Built-in retry logic for robustness.

---

## 🔧 Usage

### Basic Usage (Default LLM: `ChatLLM7`)
```python
from llmatch_validate import llmatch_validate

response = llmatch_validate(
    user_input="Your input text here..."
)
print(response)  # Returns validated/extracted data as a list
```

### Custom LLM Integration
You can replace the default `ChatLLM7` with any LangChain-compatible LLM (e.g., OpenAI, Anthropic, Google Generative AI).

#### Example: Using OpenAI
```python
from langchain_openai import ChatOpenAI
from llmatch_validate import llmatch_validate

llm = ChatOpenAI()
response = llmatch_validate(
    user_input="Your input text here...",
    llm=llm
)
print(response)
```

#### Example: Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from llmatch_validate import llmatch_validate

llm = ChatAnthropic()
response = llmatch_validate(
    user_input="Your input text here...",
    llm=llm
)
print(response)
```

#### Example: Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from llmatch_validate import llmatch_validate

llm = ChatGoogleGenerativeAI()
response = llmatch_validate(
    user_input="Your input text here...",
    llm=llm
)
print(response)
```

---

## 🔑 API Key Configuration

- **Default**: Uses `LLM7_API_KEY` from environment variables.
- **Manual Override**: Pass the API key directly:
  ```python
  response = llmatch_validate(
      user_input="Your input text here...",
      api_key="your_llm7_api_key"
  )
  ```
- **Get a Free API Key**: Register at [LLM7 Token](https://token.llm7.io/).

---

## 📌 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The input text to process and validate. |
| `api_key` | `Optional[str]` | LLM7 API key (optional if `LLM7_API_KEY` is set). |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM (optional; defaults to `ChatLLM7`). |

---

## 📝 Default LLM: `ChatLLM7`
By default, this package uses `ChatLLM7` from [`langchain_llm7`](https://pypi.org/project/langchain-llm7/). The free tier rate limits are sufficient for most use cases. For higher limits, provide your own API key.

---

## 🔄 Rate Limits
- **LLM7 Free Tier**: Sufficient for most use cases.
- **Custom API Key**: Required for higher rate limits (pass via `api_key` or `LLM7_API_KEY`).

---

## 📂 License
This project is licensed under the **MIT License**.

---

## 📧 Support & Issues
For support or bug reports, open an issue on [GitHub](https://github.com/chigwell/llmatch-validate/issues).

---

## 👤 Author
**Eugene Evstafev** ([LinkedIn](https://linkedin.com/in/eugene-evstafev)) | [GitHub](https://github.com/chigwell)

**Email**: [hi@euegne.plus](mailto:hi@euegne.plus)

---

## 📚 Related Packages
- [`llmatch-messages`](https://pypi.org/project/llmatch-messages/) (Dependency)
- [`langchain_llm7`](https://pypi.org/project/langchain-llm7/) (Default LLM)