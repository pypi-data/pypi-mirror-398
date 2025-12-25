# nl2action
[![PyPI version](https://badge.fury.io/py/nl2action.svg)](https://badge.fury.io/py/nl2action)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/nl2action)](https://pepy.tech/project/nl2action)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

A package for natural language interpretation to structured commands or actions

## Overview
This package interprets user-submitted text descriptions and converts them into structured commands or actions for devices, home automation scripts, and other applications. It utilizes pattern matching with language models to translate natural language inputs into executable instructions.

## Installation
```bash
pip install nl2action
```

## Usage
```python
from nl2action import nl2action

response = nl2action("user_input_text")
```

## Parameters

* `user_input`: The user-submitted text to process
* `llm`: The langchain llm instance to use (optional, defaults to `ChatLLM7` with `LLM7_API_KEY`)
* `api_key`: The API key for LLM7 (optional, default is environment variable `LLM7_API_KEY` or `None`)

### Using a custom LLM instance
```python
from langchain_openai import ChatOpenAI
from nl2action import nl2action

llm = ChatOpenAI()
response = nl2action(user_input, llm=llm)
```

### Using an Anthropic AI
```python
from langchain_anthropic import ChatAnthropic
from nl2action import nl2action

llm = ChatAnthropic()
response = nl2action(user_input, llm=llm)
```

### Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from nl2action import nl2action

llm = ChatGoogleGenerativeAI()
response = nl2action(user_input, llm=llm)
```

## Environment Variables

* `LLM7_API_KEY`: Set to use a custom API key for LLM7, or `None` for the free tier

## LLM7 Setup

* Get a free API key at https://token.llm7.io/
* For higher rate limits, set the `LLM7_API_KEY` environment variable or pass it directly to the `nl2action` function

## Issues
https://github.com/chigwell/ nl2action