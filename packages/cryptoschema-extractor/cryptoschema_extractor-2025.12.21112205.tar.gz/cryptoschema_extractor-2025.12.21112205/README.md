# cryptoschema-extractor
[![PyPI version](https://badge.fury.io/py/cryptoschema-extractor.svg)](https://badge.fury.io/py/cryptoschema-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cryptoschema-extractor)](https://pepy.tech/project/cryptoschema-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that extracts structured summaries of cryptographic schemes from textual descriptions.

## Overview

This system takes a textual synopsis of a cryptographic scheme and extracts a structured summary that highlights its key components, such as the types of finite fields used, the encryption process, key generation, and the mathematical principles underlying the cryptosystem. It transforms unstructured textual references into a predictable, organized format suitable for inclusion in catalogs, research summaries, or educational material.

## Installation

```bash
pip install cryptoschema_extractor
```

## Usage

### Basic Usage

```python
from cryptoschema_extractor import cryptoschema_extractor

response = cryptoschema_extractor(user_input="Your text here")
print(response)
```

### Using a Custom LLM

You can use any LLM compatible with LangChain by passing an instance of it to the `cryptoschema_extractor` function.

#### Example with OpenAI

```python
from langchain_openai import ChatOpenAI
from cryptoschema_extractor import cryptoschema_extractor

llm = ChatOpenAI()
response = cryptoschema_extractor(user_input="Your text here", llm=llm)
print(response)
```

#### Example with Anthropic

```python
from langchain_anthropic import ChatAnthropic
from cryptoschema_extractor import cryptoschema_extractor

llm = ChatAnthropic()
response = cryptoschema_extractor(user_input="Your text here", llm=llm)
print(response)
```

#### Example with Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from cryptoschema_extractor import cryptoschema_extractor

llm = ChatGoogleGenerativeAI()
response = cryptoschema_extractor(user_input="Your text here", llm=llm)
print(response)
```

### Using a Custom API Key

If you want to use a custom API key for LLM7, you can pass it directly or set it as an environment variable.

#### Passing API Key Directly

```python
from cryptoschema_extractor import cryptoschema_extractor

response = cryptoschema_extractor(user_input="Your text here", api_key="your_api_key")
print(response)
```

#### Setting API Key via Environment Variable

```bash
export LLM7_API_KEY="your_api_key"
```

```python
from cryptoschema_extractor import cryptoschema_extractor

response = cryptoschema_extractor(user_input="Your text here")
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

By default, this package uses `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/).

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly to the `cryptoschema_extractor` function. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/cryptoschema-extractor/issues).

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)