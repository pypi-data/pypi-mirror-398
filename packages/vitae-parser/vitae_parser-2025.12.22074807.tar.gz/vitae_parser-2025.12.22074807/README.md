# Vitae-Parse
[![PyPI version](https://badge.fury.io/py/vitae-parser.svg)](https://badge.fury.io/py/vitae-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vitae-parser)](https://pepy.tech/project/vitae-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for extracting and structuring biographical information from unstructured text about notable individuals.

## Overview

This package uses a combination of natural language processing (NLP) and machine learning to extract key details such as name, profession, notable facts, and dates from text sources. It's designed for researchers, biographers, and historians who need to quickly parse and organize information from text sources.

## Installation

You can install Vitae-Parse using pip:

```bash
pip install vitae_parser
```

## Usage

You can use the `vitae_parser` function to extract information from a text input. Here's an example:

```python
from vitae_parser import vitae_parser

user_input = """
John Doe is a renowned scientist who has published numerous papers on AI. He received his PhD in Computer Science from Stanford University in 2010.
"""

response = vitae_parser(user_input)
print(response)
```

The function takes in three parameters:

* `user_input`: The text input to process, which should describe a person's life, achievements, or significant events.
* `api_key`: The API key for LLM7, which is used by default if not provided. You can get a free API key by registering at https://token.llm7.io/
* `llm`: The LangChain LL&M instance to use. If not provided, the default `ChatLLM7` will be used. You can safely pass your own LLM instance if you want to use another LLM. For example, to use the OpenAI LLM:

```python
from langchain_openai import ChatOpenAI
from vitae_parser import vitae_parser

llm = ChatOpenAI()
response = vitae_parser(user_input, llm=llm)
```

## Development

This package uses the `LangChain` library to integrate with LLM7. You can find the documentation for `LangChain` at https://docs.langchain.com/. If you want to use a different LLM, you can pass your own instance of the `BaseChatModel` class.

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly.

## Contributing

Contributions are welcome! Please submit issues or pull requests through the GitHub repository: https://github.com/chigwell/vitae-parser.

## Author

Eugene Evstafev (eugene.evstafev@eugene.plus)

## License

This package is released under the MIT license.