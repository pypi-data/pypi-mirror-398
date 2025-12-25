# ProphecyPerfect
[![PyPI version](https://badge.fury.io/py/prophecyperfect.svg)](https://badge.fury.io/py/prophecyperfect)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/prophecyperfect)](https://pepy.tech/project/prophecyperfect)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for analyzing and verifying if textual statements correctly express prophetic or visionary statements in the perfect tense.

## Installation

```bash
pip install prophecyperfect
```

## Overview

The `prophecyperfect` package takes a brief textual description, prompt, or statement from the user and analyzes it to determine if it correctly expresses a prophetic or visionary statement in the perfect tense. Using pattern matching and structured responses, it classifies the input as prophetic, reaffirming its status, or identifies inaccuracies or non-prophetic phrasing.

## Usage

### Basic Usage

```python
from prophecyperfect import prophecyperfect

# Analyze a prophetic statement
user_input = "Thus saith the Lord: I will surely bless you, and I will multiply you exceedingly."
response = prophecyperfect(user_input)
print(response)
```

### Using Custom LLM

You can also use your own LLM instance from LangChain. Here are examples with different providers:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from prophecyperfect import prophecyperfect

llm = ChatOpenAI()
response = prophecyperfect(user_input, llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from prophecyperfect import prophecyperfect

llm = ChatAnthropic()
response = prophecyperfect(user_input, llm=llm)
```

#### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from prophecyperfect import prophecyperfect

llm = ChatGoogleGenerativeAI()
response = prophecyperfect(user_input, llm=llm)
```

### API Key Configuration

The default rate limits for LLM7 free tier are sufficient for most use cases. If you need higher rate limits, you can:

1. Set the API key as an environment variable:
```bash
export LLM7_API_KEY="your_api_key_here"
```

2. Or pass it directly to the function:
```python
response = prophecyperfect(user_input, api_key="your_api_key_here")
```

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)

## Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, it will use the environment variable `LLM7_API_KEY` or the default free tier.

## Author

- **Eugene Evstafev** - [hi@euegne.plus](mailto:hi@euegne.plus)
- **GitHub Nickname**: chigwell

## Issues

For any issues or to contribute, please visit the GitHub repository: [https://github.com/chigwell/prophecyperfect](https://github.com/chigwell/prophecyperfect)