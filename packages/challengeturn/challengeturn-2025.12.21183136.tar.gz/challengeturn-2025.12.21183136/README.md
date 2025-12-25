# Challeneturn
[![PyPI version](https://badge.fury.io/py/challengeturn.svg)](https://badge.fury.io/py/challengeturn)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/challengeturn)](https://pepy.tech/project/challengeturn)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

===============

A package that generates encouraging and strategic responses to user input, identifying challenges and offering tips, reframing, or positive reinforcement.

## Installation
---------------

```bash
pip install challengeturn
```

## Usage
-----

```python
from challengeturn import challengeturn

response = challengeturn(user_input="I can't do this")
```

## Documentation
--------------

### Parameters

* `user_input`: the user's input text (str)
* `llm`: an instance of `BaseChatModel` (langchain.core.language_models.BaseChatModel), defaulting to `ChatLLM7` from langchain_llm7.
* `api_key`: the API key for LLM7, defaulting to the `LLM7_API_KEY` environment variable or "None" if not provided.

### Passing your own LLM

You can safely pass your own LLM instance if desired. For example, to use the OpenAI LLM:

```python
from langchain_openai import ChatOpenAI
from challengeturn import challengeturn

llm = ChatOpenAI()
response = challengeturn(user_input, llm=llm)
```

Or the Anthropic LLM:

```python
from langchain_anthropic import ChatAnthropic
from challengeturn import challengeturn

llm = ChatAnthropic()
response = challengeturn(user_input, llm=llm)
```

Or the Google Generative AI LLM:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from challengeturn import challengeturn

llm = ChatGoogleGenerativeAI()
response = challengeturn(user_input, llm=llm)
```

### LLM7 API Key

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you require higher rate limits, you can pass your own `api_key` via environment variable `LLM7_API_KEY` or via the `challengeturn` function:

```python
response = challengeturn(user_input, api_key="your_api_key")
```

You can get a free API key by registering at https://token.llm7.io/.

## GitHub
--------

[https://github.com/chigwell/challengeturn](https://github.com/chigwell/challengeturn)

## Author
------

Eugene Evstafev
hi@eugev.plus