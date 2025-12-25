# auto_comsight
[![PyPI version](https://badge.fury.io/py/auto-comsight.svg)](https://badge.fury.io/py/auto-comsight)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/auto-comsight)](https://pepy.tech/project/auto-comsight)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Streamline the extraction and structuring of technical insights from unstructured text inputs related to autonomous computing.

## Overview

A new package designed to extract and structure technical insights from unstructured text inputs related to autonomous computing. This tool enables users to input text descriptions, research notes, or technical specifications about autonomous systems, and receive a standardized, structured output that categorizes key components, identifies potential challenges, and suggests optimization strategies.

## Features

* Extract and structure technical insights from unstructured text inputs
* Identify key components and potential challenges related to autonomous computing
* Suggest optimization strategies for autonomous systems

## Installation

```bash
pip install auto_comsight
```

## Example Usage

```python
from auto_comsight import auto_comsight
import os

# assuming API_KEY is your llm7 api key
launchpad_api_key = os.getenv("LLM7_API_KEY") or "YOUR_LLM7_API_KEY"
user_input = "example text about auto_comsight"
response = auto_comsight(user_input, api_key=launchpad_api_key)

print(response)
```

## Parameters

* `user_input` : the user input text to process
* `llm` : the langchain llm instance to use, if not provided the default ChatLLM7 will be used
* `api_key` : the api key for llm7, if not provided uses default rate limits

## LLM7 API Key

You can get a free API key by registering at https://token.llm7.io/. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly like `auto_comsight(user_input, api_key="their_api_key")`.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package.

## Supported LLM Models

auto_comsight uses the ChatLLM7 from langchain_llm7 (https://pypi.org/project/langchain-llm7/) by default. You can safely pass your own llm instance (based on https://docs.layer5.dev/llm/llm.html) via passing it like `auto_comsight(user_input, llm=their_llm_instance)`. For example, to use the openai (https://docs.layer5.dev/llm/openai.html), you can pass your own instance:

```python
from langchain_openai import ChatOpenAI
from auto_comsight import auto_comsight
llm = ChatOpenAI()
response = auto_comsight(user_input, llm=llm)
```

or for example to use the anthropic (https://docs.layer5.dev/llm/anthropic.html), you can pass your own instance:

```python
from langchain_anthropic import ChatAnthropic
from auto_comsight import auto_comsight
llm = ChatAnthropic()
response = auto_comsight(user_input, llm=llm)
```

or google (https://docs.layer5.dev/llm/google.html), you can pass your own instance:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from auto_comsight import auto_comsight
llm = ChatGoogleGenerativeAI()
response = auto_comsight(user_input, llm=llm)
```

## Contributing

Contributions are welcome! Please submit pull requests or issues to https://github.com/chigwell/auto-comsight

## Author

Eugene Evstafev
hi@euegne.plus

## Changelog

Please see [GitHub Releases](https://github.com/chigwell/auto-comsight/releases) for detailed changelog.