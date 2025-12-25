# av-safety-parser
[![PyPI version](https://badge.fury.io/py/av-safety-parser.svg)](https://badge.fury.io/py/av-safety-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/av-safety-parser)](https://pepy.tech/project/av-safety-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package for extracting and structuring aviation safety information from unstructured text.  
It parses texts such as FAA warnings and news articles to return key details (incident type, affected aircraft, safety risks, etc.) in a consistent format.

## Features

- Simple API that takes raw text and returns structured data.
- Uses the default `ChatLLM7` model from `langchain_llm7` for inference.
- Fully compatible with any LangChain LLM implementation (OpenAI, Anthropic, Google Gemini, etc.) by passing a custom instance.
- Supports API-key configuration via environment variable or explicit parameter.

## Installation

```bash
pip install av_safety_parser
```

## Quick Example

```python
from av_safety_parser import av_safety_parser

user_input = """
FAA publishes new warning on rotor blade vibrations in twin‑prop aircraft.
There were several incidents where the vibrations caused structural fatigue.
"""

# Using the default ChatLLM7
results = av_safety_parser(user_input)
print(results)
```

You can also pass a custom LLM instance:

```python
# Example with OpenAI's ChatOpenAI
from langchain_openai import ChatOpenAI
from av_safety_parser import av_safety_parser

llm = ChatOpenAI()
results = av_safety_parser(user_input, llm=llm)
print(results)
```

```python
# Example with Anthropic's ChatAnthropic
from langchain_anthropic import ChatAnthropic
from av_safety_parser import av_safety_parser

llm = ChatAnthropic()
results = av_safety_parser(user_input, llm=llm)
print(results)
```

```python
# Example with Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from av_safety_parser import av_safety_parser

llm = ChatGoogleGenerativeAI()
results = av_safety_parser(user_input, llm=llm)
print(results)
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Raw text to parse. |
| `llm` | `Optional[BaseChatModel]` | LangChain LLM instance. If omitted, `ChatLLM7` will be used automatically. |
| `api_key` | `Optional[str]` | API key for LLM7. If not provided, the library will look for the `LLM7_API_KEY` environment variable. |

> **Default Rate Limits**  
> The free tier of LLM7 offers enough rate limits for most use cases. If you require higher limits, pass your own `api_key` either through `av_safety_parser(user_input, api_key="your_key")` or by setting `LLM7_API_KEY` in your environment.

## Getting an LLM7 API Key

1. Sign up at [https://token.llm7.io/](https://token.llm7.io/)
2. Retrieve your API token
3. Set it as an environment variable:  
   ```bash
   export LLM7_API_KEY="your_token_here"
   ```

## Issue Tracker

If you encounter any problems or have feature requests, please open an issue at:  
[https://github.com/chigwell/av-safety-parser/issues](https://github.com/chigwell/av-safety-parser/issues)

## Author

- **Name:** Eugene Evstafev  
- **GitHub:** @chigwell  
- **Email:** hi@euge.ne.plus  

Enjoy using **av-safety-parser** to keep aviation data clear and consistent!