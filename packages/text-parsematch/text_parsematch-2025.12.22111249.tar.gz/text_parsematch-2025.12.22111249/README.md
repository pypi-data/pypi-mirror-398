# text-parsematch
[![PyPI version](https://badge.fury.io/py/text-parsematch.svg)](https://badge.fury.io/py/text-parsematch)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text-parsematch)](https://pepy.tech/project/text-parsematch)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for processing user-provided text input and returning structured, validated output using pattern matching and retries.

## Overview

This package ensures consistent and reliable formatting for applications like data extraction, content categorization, or structured response generation, without handling raw media files directly.

## Installation

```bash
pip install text_parsematch
```

## Usage

```python
from text_parsematch import text_parsematch

user_input = "Example text to process"
response = text_parsematch(user_input)

# To use your own LLM instance:
from langchain_core.language_models import BaseChatModel
from text_parsematch import text_parsematch

llm = BaseChatModel(...)  # create your own LLM instance
response = text_parsematch(user_input, llm=llm)

# For LLM7, you can also pass the api key:
from text_parsematch import text_parsematch

response = text_parsematch(user_input, api_key="your_api_key")

# Or use the default LLM7 instance with your api key:
from text_parsematch import text_parsematch

response = text_parsematch(user_input, api_key="your_api_key")
```

## Available LLM Models

By default, this package uses the ChatLLM7 from `langchain_llm7`. If you want to use another LLM, you can pass your own instance via the `llm` parameter.

Here are some examples with popular LLMs:

* OpenAI:
```python
from langchain_openai import ChatOpenAI
from text_parsematch import text_parsematch

llm = ChatOpenAI()
response = text_parsematch(user_input, llm=llm)
```

* Anthropic:
```python
from langchain_anthropic import ChatAnthropic
from text_parsematch import text_parsematch

llm = ChatAnthropic()
response = text_parsematch(user_input, llm=llm)
```

* Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from text_parsematch import text_parsematch

llm = ChatGoogleGenerativeAI()
response = text_parsematch(user_input, llm=llm)
```

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own api key via environment variable `LLM7_API_KEY` or via passing it directly like `text-parsematch(user_input, api_key="your_api_key")`.

## Getting a Free API Key

You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Issues

Report issues at: https://github.com/chigwell/text-parsematch

## Author

Eugene Evstafev (chigwell)
hi@eugene.plus