# TextForgePy
[![PyPI version](https://badge.fury.io/py/textforgepy.svg)](https://badge.fury.io/py/textforgepy)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/textforgepy)](https://pepy.tech/project/textforgepy)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Transform unstructured text inputs into standardized, machine-readable outputs using natural language processing (NLP) and reinforcement learning.

## Overview

TextForgePy is a Python package designed to convert free-form text inputs into structured data, perfect for domains where consistency and formatting are crucial. By leveraging LLM7, it reduces ambiguity and enhances reliability.

## Installation

```bash
pip install textforgepy
```

## Example Usage

```python
from textforgepy import textforgepy

response = textforgepy(user_input="Your user input text here")
print(response)  # response is a list of processed strings
```

## Input Parameters

* `user_input`: The user input text to process (string)
* `llm`: The langchain LLM instance to use; defaults to `ChatLLM7` from `langchain_llm7` (optional)
* `api_key`: The API key for LLM7; if not provided, uses the `LLM7_API_KEY` environment variable or defaults to "None" (optional)

Note: You can safely pass your own LLM instance by using a different langchain library, e.g.:

```python
from langchain_openai import ChatOpenAI
from textforgepy import textforgepy

llm = ChatOpenAI()
response = textforgepy(user_input, llm=llm)
```

or:

```python
from langchain_anthropic import ChatAnthropic
from textforgepy import textforgepy

llm = ChatAnthropic()
response = textforgepy(user_input, llm=llm)
```

or even:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from textforgepy import textforgepy

llm = ChatGoogleGenerativeAI()
response = textforgepy(user_input, llm=llm)
```

## Rate Limits

The default rate limits for LLM7's free tier are sufficient for most use cases of TextForgePy. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or directly like `textforgepy(user_input, api_key="your_api_key")`.

Get a free API key at https://token.llm7.io/

## Contributing

Please report issues at https://github.com/chigwell/textforgepy

Author: Eugene Evstafev
Email: hi@euegne.plus
GitHub: https://github.com/chigwell

## License

...