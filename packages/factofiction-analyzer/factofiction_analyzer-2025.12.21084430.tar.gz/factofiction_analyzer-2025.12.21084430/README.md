# Factofiction Analyzer
[![PyPI version](https://badge.fury.io/py/factofiction-analyzer.svg)](https://badge.fury.io/py/factofiction-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/factofiction-analyzer)](https://pepy.tech/project/factofiction-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

Factofiction Analyzer is a Python package that helps users distinguish between factual information and imaginative interpretations. It takes user-provided text as input, analyzes and structures the content using advanced language models, and identifies and separates factual statements from imaginative or speculative ones.

## Installation

```bash
pip install factofiction_analyzer
```

## Usage

Usage example:
```python
from factofiction_analyzer import factofiction_analyzer

response = factofiction_analyzer(user_input="The cat sat on the mat.")
```
Input parameters:

* `user_input`: The user input text to process (str)
* `llm`: The langchain LLM instance to use (Optional[BaseChatModel]). If not provided, the default ChatLLM7 will be used.
* `api_key`: The API key for LLM7 (Optional[str]). If not provided, the LLM7 free tier will be used.

Note: If you want to use a custom LLM instance, you can pass it as an argument like this:
```python
from langchain_openai import ChatOpenAI
from factofiction_analyzer import factofiction_analyzer

llm = ChatOpenAI()
response = factofiction_analyzer(user_input="The cat sat on the mat.", llm=llm)
```

## Supported LLMs

The package uses ChatLLM7 from langchain_llm7 by default. You can use other LLMs by passing your own instance:
* OpenAI: `langchain_openai.ChatOpenAI`
* Anthropic: `langchain_anthropic.ChatAnthropic`
* Google Generative AI: `langchain_google_genai.ChatGoogleGenerativeAI`

## API Key

If you need higher rate limits for LLM7, you can set the `LLM7_API_KEY` environment variable or pass your API key directly:
```python
factofiction_analyzer(user_input="The cat sat on the mat.", api_key="your_api_key")
```
You can obtain a free API key by registering at https://token.llm7.io/

## GitHub Issues

Report any issues or bugs to: https://github.com/your-github-nickname/factofiction-analyzer/issues

## Author

Written by Eugene Evstafev (hi@euegne.plus)

## Acknowledgement

This package uses the llmatch-messages package for consistent output formatting.