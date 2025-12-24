# AnnounceExtractor
[![PyPI version](https://badge.fury.io/py/announceexctractor.svg)](https://badge.fury.io/py/announceexctractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/announceexctractor)](https://pepy.tech/project/announceexctractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


AnnounceExtractor is a Python package designed to extract key details from short announcements or descriptions. It focuses on understanding the core offering and any associated benefits presented in plain text, without needing to access external links or files. The goal is to quickly identify what is being offered and its main advantages.

## Installation

```bash
pip install announceexctractor
```

## Usage

### Basic Usage

```python
from announceexctractor import announceexctractor

user_input = "Check out our new tool! It's free, no signup required, and has no watermarks."
response = announceexctractor(user_input)
print(response)
```

### Using a Custom LLM

By default, AnnounceExtractor uses the `ChatLLM7` from `langchain_llm7`. However, you can safely pass your own LLM instance if you want to use another LLM.

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from announceexctractor import announceexctractor

llm = ChatOpenAI()
response = announceexctractor(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from announceexctractor import announceexctractor

llm = ChatAnthropic()
response = announceexctractor(user_input, llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from announceexctractor import announceexctractor

llm = ChatGoogleGenerativeAI()
response = announceexctractor(user_input, llm=llm)
print(response)
```

### Using a Custom API Key

If you want to use a custom API key for LLM7, you can pass it directly or via an environment variable.

```python
from announceexctractor import announceexctractor

# Using environment variable
import os
os.environ["LLM7_API_KEY"] = "your_api_key"
response = announceexctractor(user_input)
print(response)

# Passing API key directly
response = announceexctractor(user_input, api_key="your_api_key")
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/announceexctractor/issues).

## Author

- **Eugene Evstafev** - [chigwell](https://github.com/chigwell)
- **Email**: hi@eugene.plus