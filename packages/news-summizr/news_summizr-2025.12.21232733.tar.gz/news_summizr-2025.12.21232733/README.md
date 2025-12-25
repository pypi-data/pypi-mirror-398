# news_summizr
[![PyPI version](https://badge.fury.io/py/news-summizr.svg)](https://badge.fury.io/py/news-summizr)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/news-summizr)](https://pepy.tech/project/news-summizr)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Simplify extracting structured summaries from news articles with this package.

## Overview
A new package designed to simplify extracting structured summaries from news articles. It takes a headline or brief input about recent events and generates a concise, labeled summary emphasizing key points such as the main announcement, affected products, and regional focus.

## Installation
```bash
pip install news_summizr
```

## Usage
```python
from news_summizr import news_summizr

response = news_summizr(user_input="Some news article headline", llm=None, api_key=None)
```
Input parameters:

* `user_input`: str - the user input text to process
* `llm`: Optional[BaseChatModel] - the langchain llm instance to use, if not provided the default ChatLLM7 will be used.
* `api_key`: Optional[str] - the api key for llm7, if not provided.

By default, it uses the ChatLLM7 from langchain_llm7: https://pypi.org/project/langchain-llm7/.

You can safely pass your own llm instance (based on https://docs.langchain.com/) if you want to use another LLM, via passing it like `news_summizr(user_input, llm=your_llm_instance)`.

Here are some examples of other LLMs you can use:

```python
from langchain_openai import ChatOpenAI
from news_summizr import news_summizr

llm = ChatOpenAI()
response = news_summizr(user_input, llm=llm)

from langchain_anthropic import ChatAnthropic
from news_summizr import news_summizr

llm = ChatAnthropic()
response = news_summizr(user_input, llm=llm)

from langchain_google_genai import ChatGoogleGenerativeAI
from news_summizr import news_summizr

llm = ChatGoogleGenerativeAI()
response = news_summizr(user_input, llm=llm)
```

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own api key via environment variable `LLM7_API_KEY` or via passing it directly like `news_summizr(user_input, api_key="your_api_key")`. You can get a free api key by registering at https://token.llm7.io/.

## GitHub Issues
https://github.com/chigwell/news-summizr

## Author

Eugene Evstafev
hi@euegne.plus