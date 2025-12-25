# Fractal Categorizer
[![PyPI version](https://badge.fury.io/py/fractal-categorizer.svg)](https://badge.fury.io/py/fractal-categorizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/fractal-categorizer)](https://pepy.tech/project/fractal-categorizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that processes user-provided text descriptions of fractal patterns, cellular automata configurations, or similar generative systems, and returns structured analyses or classifications.

## Overview

This package takes in text descriptions of fractal patterns, cellular automata configurations, or similar generative systems, and uses a combination of pattern matching and natural language processing to classify and analyze them.

## Installation

You can install the package via pip:

```bash
pip install fractal_categorizer
```

## Example Usage

```python
from fractal_categorizer import fractal_categorizer

response = fractal_categorizer("A fractal pattern with a Mandelbrot set")
print(response)
```

## Input Parameters

The package takes in the following input parameters:

- `user_input`: str - the user input text to process
- `llm`: Optional[BaseChatModel] - the langchain llm instance to use, if not provided the default ChatLLM7 will be used
- `api_key`: Optional[str] - the api key for llm7, if not provided

## LLM Support

The package uses the ChatLLM7 from langchain_llm7 by default. However, you can safely pass your own llm instance based on https://docs.langchain.dev/en/latest/reference.html if you want to use another LLM, via passing it like `fractal_categorizer(user_input, llm=their_llm_instance)`.

For example, to use the openai https://docs.langchain.dev/en/latest/reference.html:

```python
from langchain_openai import ChatOpenAI
from fractal_categorizer import fractal_categorizer

llm = ChatOpenAI()
response = fractal_categorizer("A fractal pattern with a Mandelbrot set", llm=llm)
print(response)
```

or for example to use the anthropic https://docs.langchain.dev/en/latest/reference.html:

```python
from langchain_anthropic import ChatAnthropic
from fractal_categorizer import fractal_categorizer

llm = ChatAnthropic()
response = fractal_categorizer("A fractal pattern with a Mandelbrot set", llm=llm)
print(response)
```

or google https://docs.langchain.dev/en/latest/reference.html:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from fractal_categorizer import fractal_categorizer

llm = ChatGoogleGenerativeAI()
response = fractal_categorizer("A fractal pattern with a Mandelbrot set", llm=llm)
print(response)
```

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7 you can pass your own api_key via environment variable LLM7_API_KEY or via passing it directly like `fractal_categorizer(user_input, api_key="their_api_key")`. You can get a free api key by registering at https://token.llm7.io/

## Contributing

Contributions are welcome! If you have any suggestions or issues, please open an issue on the GitHub repository: https://github.com/chigwell/fractal-categorizer.

## Author

Eugene Evstafev <eugene.evstafev@chigwell.plus>