# Deal Distiller

[![PyPI version](https://badge.fury.io/py/deal-distiller.svg)](https://pypi.org/project/deal-distiller)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/personalized-badge/deal-distiller?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads)](https://pepy.tech/project/deal-distiller)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/eugene-evstafev/)

## Overview

Deal Distiller is a Python package designed to distill complex business and technology news into easily digestible summaries. It focuses on the core implications and potential impact of mergers and acquisitions, providing concise, structured overviews of significant corporate events.

## Installation

```bash
pip install deal_distiller
```

## Usage

### Basic Usage

```python
from deal_distiller import deal_distiller

user_input = "Your news headline or article snippet here"
response = deal_distiller(user_input)
print(response)
```

### Using a Custom LLM

You can use any LLM compatible with LangChain by passing your own LLM instance.

#### Example with OpenAI

```python
from langchain_openai import ChatOpenAI
from deal_distiller import deal_distiller

llm = ChatOpenAI()
response = deal_distiller(user_input, llm=llm)
print(response)
```

#### Example with Anthropic

```python
from langchain_anthropic import ChatAnthropic
from deal_distiller import deal_distiller

llm = ChatAnthropic()
response = deal_distiller(user_input, llm=llm)
print(response)
```

#### Example with Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from deal_distiller import deal_distiller

llm = ChatGoogleGenerativeAI()
response = deal_distiller(user_input, llm=llm)
print(response)
```

## Parameters

- **user_input** (str): The user input text to process.
- **llm** (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- **api_key** (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

By default, Deal Distiller uses `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/).

## Rate Limits

The default rate limits for LLM7's free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter.

```python
from deal_distiller import deal_distiller

user_input = "Your news headline or article snippet here"
response = deal_distiller(user_input, api_key="your_api_key")
print(response)
```

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Author

- **Eugene Evstafev** - [chigwell](https://github.com/chigwell)
- **Email**: hi@eugene.plus

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/deal-distiller/issues).