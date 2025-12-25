# zx2xberry
[![PyPI version](https://badge.fury.io/py/zx2xberry.svg)](https://badge.fury.io/py/zx2xberry)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/zx2xberry)](https://pepy.tech/project/zx2xberry)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that enables users to control their XBerry Pi devices using a ZX Spectrum+ keyboard by translating keypresses into structured commands.

## Features

- Translates ZX Spectrum+ keyboard keypresses into structured commands for XBerry Pi devices
- Uses LLM7 by default (via `langchain_llm7`)
- Supports custom LLM instances from LangChain
- Free tier of LLM7 has sufficient rate limits for most use cases

## Installation

```bash
pip install zx2xberry
```

## Usage

### Basic Usage

```python
from zx2xberry import zx2xberry

response = zx2xberry("user input describing keypresses")
```

### Using a Custom LLM

You can use any LLM compatible with LangChain. Here are examples with different LLMs:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from zx2xberry import zx2xberry

llm = ChatOpenAI()
response = zx2xberry("user input", llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from zx2xberry import zx2xberry

llm = ChatAnthropic()
response = zx2xberry("user input", llm=llm)
```

#### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from zx2xberry import zx2xberry

llm = ChatGoogleGenerativeAI()
response = zx2xberry("user input", llm=llm)
```

### Using a Custom API Key

You can provide your own API key for LLM7 either via environment variable or directly:

```python
from zx2xberry import zx2xberry

# Via environment variable
import os
os.environ["LLM7_API_KEY"] = "your_api_key"
response = zx2xberry("user input")

# Directly
response = zx2xberry("user input", api_key="your_api_key")
```

## Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. Defaults to `ChatLLM7`.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, it will use the environment variable `LLM7_API_KEY` or the default LLM7 key.

## Returns

A list of structured commands that the XBerry Pi can interpret and execute.

## Getting an LLM7 API Key

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/zx2xberry/issues).

## Author

**Eugene Evstafev**

- Email: hi@eugene.plus
- GitHub: [chigwell](https://github.com/chigwell)