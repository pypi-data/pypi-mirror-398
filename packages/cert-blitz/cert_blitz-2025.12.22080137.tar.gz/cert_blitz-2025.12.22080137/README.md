# Cert-Blitz
[![PyPI version](https://badge.fury.io/py/cert-blitz.svg)](https://badge.fury.io/py/cert-blitz)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cert-blitz)](https://pepy.tech/project/cert-blitz)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Cert-Blitz is a Python package that decodes and analyzes digital certificates and TLS server configurations from text input. It extracts and validates structured information like issuer, subject, validity dates, and encryption algorithms, providing clear, formatted outputs that highlight key certificate properties, expiration warnings, and potential security issues.

## Installation

```bash
pip install cert_blitz
```

## Usage

### Basic Usage

```python
from cert_blitz import cert_blitz

user_input = """
-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAL8...
-----END CERTIFICATE-----
"""

response = cert_blitz(user_input)
print(response)
```

### Using a Custom LLM

You can use any LLM compatible with LangChain. Here are examples using different LLMs:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from cert_blitz import cert_blitz

llm = ChatOpenAI()
response = cert_blitz(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from cert_blitz import cert_blitz

llm = ChatAnthropic()
response = cert_blitz(user_input, llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from cert_blitz import cert_blitz

llm = ChatGoogleGenerativeAI()
response = cert_blitz(user_input, llm=llm)
print(response)
```

### Using LLM7 API Key

By default, Cert-Blitz uses the LLM7 API. You can pass your API key directly or via an environment variable.

#### Passing API Key Directly

```python
from cert_blitz import cert_blitz

response = cert_blitz(user_input, api_key="your_api_key")
print(response)
```

#### Using Environment Variable

```bash
export LLM7_API_KEY="your_api_key"
```

```python
from cert_blitz import cert_blitz

response = cert_blitz(user_input)
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

Cert-Blitz uses [ChatLLM7](https://pypi.org/project/langchain-llm7/) from `langchain_llm7` by default. You can safely pass your own LLM instance if you want to use another LLM.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/cert-blitz/issues).

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)