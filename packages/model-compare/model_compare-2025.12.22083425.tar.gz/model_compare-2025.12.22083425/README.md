# Model Compare Package
[![PyPI version](https://badge.fury.io/py/model-compare.svg)](https://badge.fury.io/py/model-compare)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/model-compare)](https://pepy.tech/project/model-compare)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A new package that helps users compare and evaluate different AI language models by analyzing their performance and capabilities.

## Overview

This package takes user-provided text input describing specific tasks or scenarios and returns a structured comparison of how different models, like Gemini 3 Flash and Claude Code, would handle those tasks. It focuses on providing objective, side-by-side evaluations based on criteria such as accuracy, creativity, and efficiency, helping users make informed decisions about which model to use for their specific needs.

## Installation

```bash
pip install model_compare
```

## Usage

```python
from model_compare import model_compare

response = model_compare(
    user_input="Compare Gemini 3 Flash and Claude Code on a text-to-image generation task",
    api_key="your_llm7_api_key",
    llm=None  # optional, defaults to ChatLLM7
)
```

You can also pass your own `BaseChatModel` instance, e.g., to use a different LLM like OpenAI:

```python
from langchain_openai import ChatOpenAI
from model_compare import model_compare

llm = ChatOpenAI()
response = model_compare(
    user_input="Compare Gemini 3 Flash and Claude Code on a text-to-image generation task",
    llm=llm
)
```

Or to use Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from model_compare import model_compare

llm = ChatAnthropic()
response = model_compare(
    user_input="Compare Gemini 3 Flash and Claude Code on a text-to-image generation task",
    llm=llm
)
```

Or to use Google Generative AI:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from model_compare import model_compare

llm = ChatGoogleGenerativeAI()
response = model_compare(
    user_input="Compare Gemini 3 Flash and Claude Code on a text-to-image generation task",
    llm=llm
)
```

You can also pass your own API key via the environment variable `LLM7_API_KEY` or directly as an argument.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via environment variable `LLM7_API_KEY` or directly as an argument.

## Getting Started

You can get a free API key by registering at https://token.llm7.io/

## Contributing

Please submit issues and pull requests to https://github.com/chigwell/model-compare

## Author

Eugene Evstafev (eugene.evstafev-plus@email.com)

## License

This package is licensed under the MIT License.