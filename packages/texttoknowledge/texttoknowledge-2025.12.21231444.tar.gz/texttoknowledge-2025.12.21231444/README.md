# texttoknowledge
[![PyPI version](https://badge.fury.io/py/texttoknowledge.svg)](https://badge.fury.io/py/texttoknowledge)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/texttoknowledge)](https://pepy.tech/project/texttoknowledge)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**texttoknowledge** is a lightweight Python package that transforms unstructured text from documents into structured, query‑able knowledge. By leveraging the `llmatch-messages` library and a language model (LLM), the package extracts key information and organizes it into predefined formats, making critical details easy to retrieve and keep up‑to‑date.

## Features

- **Simple API** – Call a single function with your raw text.
- **Customizable LLM** – Use the default `ChatLLM7` or provide any LangChain‑compatible LLM (OpenAI, Anthropic, Google, etc.).
- **Regex‑driven output** – Guarantees that the extracted data conforms to a pattern you define.
- **No boilerplate** – Handles LLM initialization, API key resolution, and error handling for you.

## Installation

```bash
pip install texttoknowledge
```

## Quick Start

```python
from texttoknowledge import texttoknowledge

# Your raw document text
raw_text = """
Project Alpha:
- Owner: Alice
- Deadline: 2025-03-15
- Status: In progress
"""

# Extract structured knowledge
structured_data = texttoknowledge(user_input=raw_text)

print(structured_data)
```

## API Reference

### `texttoknowledge(user_input: str, api_key: Optional[str] = None, llm: Optional[BaseChatModel] = None) -> List[str]`

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The raw text from which knowledge will be extracted. |
| `llm` | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the function creates a `ChatLLM7` instance automatically. |
| `api_key` | `Optional[str]` | API key for the default `ChatLLM7`. If omitted, the function reads the environment variable `LLM7_API_KEY`. |

**Returns:** `List[str]` – Extracted pieces of knowledge that match the predefined regex pattern.

## Using a Custom LLM

You can pass any LangChain‑compatible LLM that adheres to `BaseChatModel`. Below are a few examples:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from texttoknowledge import texttoknowledge

llm = ChatOpenAI()  # Configure as needed
response = texttoknowledge(user_input="Your document text here", llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from texttoknowledge import texttoknowledge

llm = ChatAnthropic()
response = texttoknowledge(user_input="Your document text here", llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from texttoknowledge import texttoknowledge

llm = ChatGoogleGenerativeAI()
response = texttoknowledge(user_input="Your document text here", llm=llm)
```

## Default LLM – ChatLLM7

If you do **not** provide an LLM, `texttoknowledge` automatically uses `ChatLLM7` from the `langchain_llm7` package:

```python
from langchain_llm7 import ChatLLM7
```

The free tier of LLM7 offers generous rate limits suitable for most use cases. To increase limits, simply supply your own API key:

```python
response = texttoknowledge(user_input="...", api_key="YOUR_LLM7_API_KEY")
```

You can obtain a free API key by registering at **https://token.llm7.io/**.

## Environment Variables

- `LLM7_API_KEY` – If set, the package will use this key for the default `ChatLLM7` instance.

## Contributing & Issues

If you encounter bugs or have feature requests, please open an issue:

**GitHub Issues:** https://github....

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev** – [chigwell](https://github.com/chigwell)  
  Email: <hi@euegne.plus>

---

Happy structuring! 🎉