# perf-metric-xtr
[![PyPI version](https://badge.fury.io/py/perf-metric-xtr.svg)](https://badge.fury.io/py/perf-metric-xtr)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/perf-metric-xtr)](https://pepy.tech/project/perf-metric-xtr)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Extract and structure key performance metrics from technology announcements.

## Overview
A new package that takes raw text input about product launches and returns a standardized output highlighting specific performance improvements.

## Installation
```bash
pip install perf_metric_xtr
```

## Example of Usage
```python
from perf_metric_xtr import perf_metric_xtr

response = perf_metric_xtr(user_input="Moore Threads unveils next-gen gaming GPU with 15x performance, 50x ray tracing")
print(response)
```

## Parameters

- `user_input` (str): the user input text to process
- `llm` (Optional[BaseChatModel]): the langchain llm instance to use, if not provided the default ChatLLM7 will be used
- `api_key` (Optional[str]): the api key for llm7, if not provided Also, you can safely pass your own llm instance (based on https://docs.langchain.com/docs/custom-forwards-llms) if you want to use another LLM, via passing it like `perf_metric_xtr(user_input, llm=your_llm_instance)`, for example to use the openai https://docs$langchain_openai
```python
from langchain_openai import ChatOpenAI
from perf_metric_xtr import perf_metric_xtr

llm = ChatOpenAI()
response = perf_metric_xtr(user_input, llm=llm)
```
or for example to use the anthropic https://docs.langchain.com/forward/docs/anthropic
```python
from langchain_anthropic import ChatAnthropic
from perf_metric_xtr import perf_metric_xtr

llm = ChatAnthropic()
response = perf_metric_xtr(user_input, llm=llm)
```
or google https://docs.langchain.com/docs/google-genai-forward
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from perf_metric_xtr import perf_metric_xtr

llm = ChatGoogleGenerativeAI()
response = perf_metric_xtr(user_input, llm=llm)
```

## Rate Limits
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7 you can pass your own api_key via environment variable `LLM7_API_KEY` or via passing it directly like `perf_metric_xtr(user_input, api_key="your_api_key")`. You can get a free api key by registering at https://token.llm7.io/

## GitHub Issues
https://github.com/chigwell/perf-metric-xtr

## Author
Eugene Evstafev
hi@euegne.plus