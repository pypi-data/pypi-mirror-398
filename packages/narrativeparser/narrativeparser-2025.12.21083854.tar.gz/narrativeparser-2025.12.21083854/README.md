# narrativeparser
[![PyPI version](https://badge.fury.io/py/narrativeparser.svg)](https://badge.fury.io/py/narrativeparser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/narrativeparser)](https://pepy.tech/project/narrativeparser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for analyzing and understanding nuanced narratives by distinguishing between factual accounts and imaginative interpretations.

## Installation

```bash
pip install narrativeparser
```

## Usage

The package provides a function `narrativeparser` that processes input text and returns a structured representation separating factual and imaginative elements.

### Basic Example

```python
from narrativeparser import narrativeparser

user_input = "Your text to analyze here..."
result = narrativeparser(user_input)
print(result)
```

### Using a Custom LLM

You can use any LangChain-compatible LLM by passing it to the `llm` parameter:

```python
from langchain_openai import ChatOpenAI
from narrativeparser import narrativeparser

llm = ChatOpenAI()
user_input = "Your text to analyze here..."
response = narrativeparser(user_input, llm=llm)
```

```python
from langchain_anthropic import ChatAnthropic
from narrativeparser import narrativeparser

llm = ChatAnthropic()
user_input = "Your text to analyze here..."
response = narrativeparser(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from narrativeparser import narrativeparser

llm = ChatGoogleGenerativeAI()
user_input = "Your text to analyze here..."
response = narrativeparser(user_input, llm=llm)
```

### API Key Configuration

The package uses [ChatLLM7](https://pypi.org/project/langchain-llm7/) by default. You can provide your API key in multiple ways:

1. Via environment variable:
```bash
export LLM7_API_KEY="your_api_key_here"
```

2. Directly in code:
```python
from narrativeparser import narrativeparser

user_input = "Your text to analyze here..."
response = narrativeparser(user_input, api_key="your_api_key_here")
```

Get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)

## Parameters

- `user_input` (str): The text input to process
- `llm` (Optional[BaseChatModel]): LangChain LLM instance (defaults to ChatLLM7)
- `api_key` (Optional[str]): API key for LLM7 (if using default LLM)

## Default LLM

The package uses ChatLLM7 by default, which provides sufficient rate limits for most use cases. For higher rate limits, provide your own API key.

## Issues

Report issues and feature requests at [GitHub Issues](https://github.com/chigwell/narrativeparser/issues)

## Author

Eugene Evstafev - hi@euegne.plus