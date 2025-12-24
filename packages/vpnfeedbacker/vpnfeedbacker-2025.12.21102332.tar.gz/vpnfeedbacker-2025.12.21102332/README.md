# VPNFeedbacker
[![PyPI version](https://badge.fury.io/py/vpnfeedbacker.svg)](https://badge.fury.io/py/vpnfeedbacker)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vpnfeedbacker)](https://pepy.tech/project/vpnfeedbacker)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Simplify and structure user feedback about VPN sign-up experiences with this package.

## Overview

VPNFeedbacker takes text input from users describing their sign-up process with a VPN service and returns a structured output categorizing the feedback into key aspects like simplicity, speed, and user satisfaction.

## Installation

```bash
pip install vpnfeedbacker
```

## Usage

```python
from vpnfeedbacker import vpnfeedbacker

response = vpnfeedbacker(user_input)
```

Or with a custom LLModel instance (based on [langchain](https://docs.langchain.com/)):
```python
from langchain_openai import ChatOpenAI
from vpnfeedbacker import vpnfeedbacker

llm = ChatOpenAI()
response = vpnfeedbacker(user_input, llm=llm)
```

## Parameters

* `user_input`: `str`, the user input text to process
* `llm`: `Optional[BaseChatModel]`, the langchain LLm instance to use. If not provided, the default `ChatLLM7` will be used.
* `api_key`: `Optional[str]`, the API key for LLM7. If not provided, it defaults to `None` or the value of the `LLM7_API_KEY` environment variable.

## Defaults

By default, the package uses the `ChatLLM7` instance from [langchain_llm7](https://pypi.org/project/langchain_llm7/).

## Custom LLMs

You can use other LLMs from [langchain](https://docs.langchain.com/) by passing your own LLm instance, e.g. OpenAI, Anthropic, Google Generative AI:
```python
from langchain_openai import ChatOpenAI
from vpnfeedbacker import vpnfeedbacker

llm = ChatOpenAI()
response = vpnfeedbacker(user_input, llm=llm)
```

or
```python
from langchain_anthropic import ChatAnthropic
from vpnfeedbacker import vpnfeedbacker

llm = ChatAnthropic()
response = vpnfeedbacker(user_input, llm=llm)
```

or
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vpnfeedbacker import vpnfeedbacker

llm = ChatGoogleGenerativeAI()
response = vpnfeedbacker(user_input, llm=llm)
```

## LLM7 Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or directly like `vpnfeedbacker(user_input, api_key="your_api_key")`. Get a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Contributing

Open issues and pull requests are welcome at [https://github.com/chigwell/vpnfeedbacker](https://github.com/chigwell/vpnfeedbacker).

## Author

Eugene Evstafev
hi@eugene.plus