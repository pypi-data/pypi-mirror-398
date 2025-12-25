# tp-llmatch-formatter
[![PyPI version](https://badge.fury.io/py/tp-llmatch-formatter.svg)](https://badge.fury.io/py/tp-llmatch-formatter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/tp-llmatch-formatter)](https://pepy.tech/project/tp-llmatch-formatter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Textpattern CMS content management package designed to streamline content formatting tasks using LLM7.

## Overview

This package allows users to input text-based content or instructions related to their Textpattern CMS, such as article drafts, formatting queries, or template adjustments. The package processes this input using llmatch-messages to ensure the output adheres to specific structured formats required by Textpattern, such as article tags, template syntax, or formatting rules. This ensures that the content or instructions are correctly formatted and ready for integration into the CMS, reducing manual errors and improving efficiency in content management workflows.

## Installation

```bash
pip install tp_llmatch_formatter
```

## Usage

### Basic Usage

```python
from tp_llmatch_formatter import tp_llmatch_formatter

response = tp_llmatch_formatter(user_input="Your text input here")
```

### Using a Custom LLM

You can use any LLM compatible with LangChain. Here are examples using different LLMs:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from tp_llmatch_formatter import tp_llmatch_formatter

llm = ChatOpenAI()
response = tp_llmatch_formatter(user_input="Your text input here", llm=llm)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from tp_llmatch_formatter import tp_llmatch_formatter

llm = ChatAnthropic()
response = tp_llmatch_formatter(user_input="Your text input here", llm=llm)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from tp_llmatch_formatter import tp_llmatch_formatter

llm = ChatGoogleGenerativeAI()
response = tp_llmatch_formatter(user_input="Your text input here", llm=llm)
```

### Using LLM7 API Key

By default, the package uses the LLM7 API. You can pass your API key directly or via an environment variable.

#### Using Environment Variable

```python
import os
from tp_llmatch_formatter import tp_llmatch_formatter

os.environ["LLM7_API_KEY"] = "your_api_key"
response = tp_llmatch_formatter(user_input="Your text input here")
```

#### Passing API Key Directly

```python
from tp_llmatch_formatter import tp_llmatch_formatter

response = tp_llmatch_formatter(user_input="Your text input here", api_key="your_api_key")
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the package will use the environment variable `LLM7_API_KEY` or a default value.

## Default LLM

The package uses [ChatLLM7](https://pypi.org/project/langchain-llm7/) from `langchain_llm7` by default. You can safely pass your own LLM instance if you want to use another LLM.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/tp-llmatch-formatter/issues).

## Author

- **Eugene Evstafev**
  - Email: hi@eugene.plus
  - GitHub: [chigwell](https://github.com/chigwell)