# Econ-Legalizer
[![PyPI version](https://badge.fury.io/py/econ-legalizer.svg)](https://badge.fury.io/py/econ-legalizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/econ-legalizer)](https://pepy.tech/project/econ-legalizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Econ-Legalizer is a Python package designed to facilitate the extraction of structured summaries and key insights from user-provided text inputs related to regional economic and legal issues, such as property rights in specific locations. It leverages advanced pattern matching and retry mechanisms to ensure accurate, consistent, and reliable information retrieval.

## Features

- Extract structured summaries from text inputs
- Focus on regional economic and legal issues
- Advanced pattern matching for accurate information retrieval
- Retry mechanisms for consistent results
- Support for custom LLM instances

## Installation

```bash
pip install econ_legalizer
```

## Usage

### Basic Usage

```python
from econ_legalizer import econ_legalizer

response = econ_legalizer("Your text input here")
print(response)
```

### Using a Custom LLM

Econ-Legalizer uses `ChatLLM7` from `langchain_llm7` by default. However, you can safely pass your own LLM instance if you want to use another LLM.

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from econ_legalizer import econ_legalizer

llm = ChatOpenAI()
response = econ_legalizer("Your text input here", llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from econ_legalizer import econ_legalizer

llm = ChatAnthropic()
response = econ_legalizer("Your text input here", llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from econ_legalizer import econ_legalizer

llm = ChatGoogleGenerativeAI()
response = econ_legalizer("Your text input here", llm=llm)
print(response)
```

### Using an API Key

If you want to use a specific API key for LLM7, you can pass it directly or set it as an environment variable.

```python
from econ_legalizer import econ_legalizer

# Passing the API key directly
response = econ_legalizer("Your text input here", api_key="your_api_key")
print(response)

# Setting the API key as an environment variable
import os
os.environ["LLM7_API_KEY"] = "your_api_key"
response = econ_legalizer("Your text input here")
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call.

## Getting an API Key

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/econ-legalizer/issues).

## Author

- **Eugene Evstafev**
  - Email: hi@eugene.plus
  - GitHub: [chigwell](https://github.com/chigwell)