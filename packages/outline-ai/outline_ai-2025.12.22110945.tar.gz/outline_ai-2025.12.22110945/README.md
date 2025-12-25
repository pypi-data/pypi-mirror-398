# outline-ai
[![PyPI version](https://badge.fury.io/py/outline-ai.svg)](https://badge.fury.io/py/outline-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/outline-ai)](https://pepy.tech/project/outline-ai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Transform user-provided text inputs into well-structured summaries, proposals, or content outlines with outline-ai.

## Introduction

outline-ai is a new package designed to revolutionize the way you create content. By leveraging language models, it generates organized and clear outputs without the need for managing media or direct document uploads. This makes it an efficient and customizable alternative to traditional platforms like Substack.

## Installation

```bash
pip install outline_ai
```

## Usage

```python
from outline_ai import outline_ai

user_input = "Create a summary of this article about AI and machine learning"
response = outline_ai(user_input)
print(response)
```

### Parameters

- `user_input`: str - The user input text to process
- `llm`: Optional[BaseChatModel] - The langchain llm instance to use, if not provided the default ChatLLM7 will be used.
- `api_key`: Optional[str] - The API key for LLM7, if not provided

By default, outline_ai uses the ChatLLM7 from langchain_llm7 (https://pypi.org/project/langchain-llm7/). If you want to use another LLM, you can safely pass your own llm instance by setting it like this:

```python
from langchain_openai import ChatOpenAI
from outline_ai import outline_ai

llm = ChatOpenAI()
response = outline_ai(user_input, llm=llm)
```

For example, to use the openai (https://pypi.org/project/langchain-openai/):

```python
from langchain_openai import ChatOpenAI
from outline_ai import outline_ai

llm = ChatOpenAI()
response = outline_ai(user_input, llm=llm)
```

Or, to use the anthropic (https://pypi.org/project/langchain-anthropic/):

```python
from langchain_anthropic import ChatAnthropic
from outline_ai import outline_ai

llm = ChatAnthropic()
response = outline_ai(user_input, llm=llm)
```

Or, to use the google (https://pypi.org/project/langchain-google-genai/):

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from outline_ai import outline_ai

llm = ChatGoogleGenerativeAI()
response = outline_ai(user_input, llm=llm)
```

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or directly. Get a free API key by registering at https://token.llm7.io/.

## GitHub

Check out the GitHub issues page for any further questions or issues: https://github.com/chigwell/outline-ai/issues

## Author

This package was created by Eugene Evstafev, you can contact him at hi@euegne.plus.

## Credits

Author: chigwell