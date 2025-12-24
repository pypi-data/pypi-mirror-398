# ISBN-Transformer
[![PyPI version](https://badge.fury.io/py/isbn-transformer.svg)](https://badge.fury.io/py/isbn-transformer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/isbn-transformer)](https://pepy.tech/project/isbn-transformer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


ISBN-Transformer is a Python package that transforms raw ISBN data into structured, visualizable formats. It is designed for librarians, book retailers, or anyone managing large book inventories, enabling quick insights and efficient data handling.

## Features

- Transforms raw ISBN data into structured, machine-readable output
- Ensures consistent formatting and reliable data extraction
- Supports visualization of book inventory data
- Integrates seamlessly with LangChain's LLM ecosystem

## Installation

```bash
pip install isbn_transformer
```

## Usage

### Basic Usage

```python
from isbn_transformer import isbn_transformer

user_input = "Your raw ISBN data here"
response = isbn_transformer(user_input)
print(response)
```

### Using a Custom LLM

You can use any LLM compatible with LangChain. Here are examples using different LLMs:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from isbn_transformer import isbn_transformer

llm = ChatOpenAI()
response = isbn_transformer(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from isbn_transformer import isbn_transformer

llm = ChatAnthropic()
response = isbn_transformer(user_input, llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from isbn_transformer import isbn_transformer

llm = ChatGoogleGenerativeAI()
response = isbn_transformer(user_input, llm=llm)
print(response)
```

### Using LLM7 API Key

By default, the package uses the LLM7 API. You can pass your API key via an environment variable or directly in the function call.

#### Using Environment Variable

```python
import os
from isbn_transformer import isbn_transformer

os.environ["LLM7_API_KEY"] = "your_api_key"
response = isbn_transformer(user_input)
print(response)
```

#### Directly Passing API Key

```python
from isbn_transformer import isbn_transformer

response = isbn_transformer(user_input, api_key="your_api_key")
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the package will use the default or the one set in the environment variable `LLM7_API_KEY`.

## Rate Limits

The default rate limits for LLM7's free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call.

## Getting an API Key

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/isbn-transformer/issues).

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)