# Techsummarizer
[![PyPI version](https://badge.fury.io/py/techsummarizer.svg)](https://badge.fury.io/py/techsummarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/techsummarizer)](https://pepy.tech/project/techsummarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for summarizing technical articles and announcements by extracting structured key information from user-provided text.

## Overview

This package leverages language models to identify and organize important details such as product features, specifications, release dates, and relevant contextual data, providing a concise and structured overview of complex technical content.

## Installation

```bash
pip install techsummarizer
```

## Usage

```python
from techsummarizer import techsummarizer

response = techsummarizer(
    user_input="user input text here",
    api_key="your_api_key_here"  # if not provided, defaults to LLM7 free tier
)
```

You can also pass your own LLM instance (e.g., OpenAI, Anthropic, Google Generative AI) for more control:
```python
from langchain_openai import ChatOpenAI
from techsummarizer import techsummarizer

llm = ChatOpenAI()
response = techsummarizer(
    user_input="user input text here",
    llm=llm
)
```
Or with Anthropic:
```python
from langchain_anthropic import ChatAnthropic
from techsummarizer import techsummarizer

llm = ChatAnthropic()
response = techsummarizer(
    user_input="user input text here",
    llm=llm
)
```
Or with Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from techsummarizer import techsummarizer

llm = ChatGoogleGenerativeAI()
response = techsummarizer(
    user_input="user input text here",
    llm=llm
)
```
## Default LLM

This package uses the ChatLLM7 from langchain_llm7 by default. You can safely pass your own LLM instance if you want to use another LLM.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or directly:
```python
techsummarizer(
    user_input="user input text here",
    api_key="your_api_key_here"
)
```
You can get a free API key by registering at https://token.llm7.io/

## Issues

Report any issues or bugs to: https://github.com/chigwell/techsummarizer

## Author

Eugene Evstafev
hi@euegne.plus