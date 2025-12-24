# Vote Clarify
[![PyPI version](https://badge.fury.io/py/voteclarify.svg)](https://badge.fury.io/py/voteclarify)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/voteclarify)](https://pepy.tech/project/voteclarify)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

A package for processing user queries about why small voting or ranking projects get flagged as spam so easily.

## Overview
This package uses natural language processing to understand the input and generates a structured response with insights and potential solutions. It leverages the capabilities of llmatch-messages to ensure the response is consistent and formatted correctly, making it easier for users to understand the issue and find solutions.

## Installation
```bash
pip install voteclarify
```

## Usage
```python
from voteclarify import voteclarify

user_input = "My small voting project gets flagged as spam, why?"
response = voteclarify(user_input)
print(response)
```
You can pass additional parameters to customize the behavior:
```python
from voteclarify import voteclarify
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_llm7 import ChatLLM7
from langchain_openai import ChatOpenAI

user_input = "My small voting project gets flagged as spam, why?"
llm = ChatOpenAI()
response = voteclarify(user_input, llm=llm)
print(response)
```
You can also use your own LLM instance, for example:
```python
from voteclarify import voteclarify
from langchain_openai import ChatOpenAI

user_input = "My small voting project gets flagged as spam, why?"
llm = ChatOpenAI()
response = voteclarify(user_input, llm=llm)
print(response)
```
Or use the Anthropic or Google Generative AI:
```python
from voteclarify import voteclarify
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

user_input = "My small voting project gets flagged as spam, why?"
llm = ChatAnthropic()
response = voteclarify(user_input, llm=llm)
print(response)
```

## API Key
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly:
```python
from voteclarify import voteclarify

user_input = "My small voting project gets flagged as spam, why?"
response = voteclarify(user_input, api_key="your_api_key")
print(response)
```
You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Limitations
This package is designed to handle common issues with small voting or ranking projects. However, it is not a substitute for professional moderation or review. Always review the output carefully and take necessary actions to ensure the integrity and security of your project.

## Contributing
Feel free to contribute to this package by submitting pull requests or opening issues on the [GitHub page](https://github.com/chigwell/voteclarify).

## Author
Eugene Evstafev (<hi@eugene.plus>)