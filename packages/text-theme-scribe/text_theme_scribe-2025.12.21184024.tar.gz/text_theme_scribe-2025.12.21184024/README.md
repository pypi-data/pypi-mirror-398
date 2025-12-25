# text_theme_scribe
[![PyPI version](https://badge.fury.io/py/text-theme-scribe.svg)](https://badge.fury.io/py/text-theme-scribe)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text-theme-scribe)](https://pepy.tech/project/text-theme-scribe)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A package that analyzes user-provided text to identify and extract recurring themes or topics, then summarizes them into a structured list of key concepts.

## Installation

To install the package, use pip:
```bash
pip install text-theme_scribe
```

## Usage

To use the package, import the `text_theme_scribe` function and call it with a string input:
```python
from text_theme_scribe import text_theme_scribe

user_input = "This is a sample text with multiple themes..."
response = text_theme_scribe(user_input)
print(response)
```

## Parameters

* `user_input`: str, the user input text to process
* `llm`: Optional[BaseChatModel], the langchain LLM instance to use (default: ChatLLM7 from langchain_llm7 https://pypi.org/project/langchain_llm7/)
* `api_key`: Optional[str], the API key for llm7 (default: environment variable LLM7_API_KEY)

You can pass a custom LLM instance by passing it as the `llm` parameter. For example:
```python
from text_theme_scribe import text_theme_scribe
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
response = text_theme_scribe(user_input, llm=llm)
```

You can also pass a custom API key by setting the `LLM7_API_KEY` environment variable or by passing it directly:
```python
import os
os.environ["LLM7_API_KEY"] = "your_api_key"
response = text_theme_scribe(user_input)
```

If you want to use a different LLM, you can use a different API key:
```python
response = text_theme_scribe(user_input, api_key="your_api_key")
```

## Default LLM and API Key

By default, the package uses the ChatLLM7 from langchain_llm7 https://pypi.org/project/langchain_llm7/ and the free tier API key. If you want to use a different LLM or has higher rate limits, you can pass a custom LLM instance or API key.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable LLM7_API_KEY or by passing it directly.

## Author

**Eugene Evstafev**

You can get a free API key by registering at https://token.llm7.io/

## GitHub Issues

If you find any issues or have any questions, please open an issue on our GitHub repository: https://github.com/chigwell/text-theme_scribe