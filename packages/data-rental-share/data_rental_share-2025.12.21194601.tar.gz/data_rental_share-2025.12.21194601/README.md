# data_rental_share
[![PyPI version](https://badge.fury.io/py/data-rental-share.svg)](https://badge.fury.io/py/data-rental-share)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/data-rental-share)](https://pepy.tech/project/data-rental-share)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

A package for securely and temporarily sharing structured data with others on a rental basis.

## Overview
A command-line tool that enables users to easily and securely share text-based data descriptions or access requests, ensuring that shared information is formatted consistently and access terms are clearly defined.

## Installation
```bash
pip install data_rental_share
```

## Usage
```python
from data_rental_share import data_rental_share

response = data_rental_share(user_input="Your text-based data description or access request")
```
You can pass an optional `llm` parameter to use a custom LLM instance:
```python
from langchain_openai import ChatOpenAI
from data_rental_share import data_rental_share

llm = ChatOpenAI()
response = data_rental_share(user_input="Your text-based data description or access request", llm=llm)
```
You can also pass an optional `api_key` parameter to use a custom LLM7 API key:
```python
from data_rental_share import data_rental_share

response = data_rental_share(user_input="Your text-based data description or access request", api_key="your_api_key")
```

## Defaults
This package uses the ChatLLM7 from langchain_llm7 by default. You can safely pass your own LLM instance (based on https://docs.langchain.dev/en/latest/provider.html) by passing it like `data_rental_share(user_input, llm=their_llm_instance)`.

## Rate Limits
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via environment variable LLM7_API_KEY or via passing it directly like `data_rental_share(user_input, api_key="your_api_key")`. You can get a free API key by registering at https://token.llm7.io/.

## Documentation
For more information about the llm7 API, please visit https://docs.llm7.io/.

## GitHub Issues
If you encounter an issue, please report it at https://github.com/chigwell/data-rental-share/issues

## Author
Eugene Evstafev
hi@euegne.plus
chigwell