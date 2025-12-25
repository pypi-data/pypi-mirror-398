# Release Extractor
[![PyPI version](https://badge.fury.io/py/release-extractor.svg)](https://badge.fury.io/py/release-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/release-extractor)](https://pepy.tech/project/release-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Release Extractor is a Python package designed to transform unstructured or semi-structured text updates about technology releases into clear, structured summaries. It extracts key details such as version numbers, release date, and main features using pattern matching, enabling automated, consistent processing of release information.

## Features

- Extracts key details from technology release announcements
- Supports custom LLM integration
- Uses pattern matching for consistent results
- Lightweight and easy to integrate

## Installation

```bash
pip install release_extractor
```

## Usage

### Basic Usage

```python
from release_extractor import release_extractor

user_input = "New version 2.1.0 of Awesome Software is out with exciting features!"
response = release_extractor(user_input)
print(response)
```

### Advanced Usage with Custom LLM

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from release_extractor import release_extractor

llm = ChatOpenAI()
response = release_extractor(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from release_extractor import release_extractor

llm = ChatAnthropic()
response = release_extractor(user_input, llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from release_extractor import release_extractor

llm = ChatGoogleGenerativeAI()
response = release_extractor(user_input, llm=llm)
print(response)
```

## Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

By default, the package uses `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/). You can safely pass your own LLM instance if you want to use another LLM.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter.

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/release-extractor/issues).

## Author

- **Eugene Evstafev** - [chigwell](https://github.com/chigwell)
- Email: hi@euegne.plus