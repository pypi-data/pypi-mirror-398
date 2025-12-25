# Headline Parser
[![PyPI version](https://badge.fury.io/py/headline-parser.svg)](https://badge.fury.io/py/headline-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/headline-parser)](https://pepy.tech/project/headline-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A package to process news headlines or short text snippets, extracting key entities, topics, and sentiment, and outputting structured summaries in a consistent format.

## Installation

```bash
pip install headline_parser
```

## Overview

This package uses a large language model (LLM) to process input text and generate structured summaries of current events. It's suitable for:
- News aggregation
- Content moderation analysis
- Tracking public discourse on free speech and regulatory issues
- Applications not requiring raw media files

## Example usage

```python
from headline_parser import headline_parser

response = headline_parser(
    user_input="Us Democrats pass a health care reform bill.",
)
print(response)
```

The `headline_parser` function can take in optional arguments:
- `llm`: an instance of `langchain_core.language_models.BaseChatModel`, which defaults to `langchain_llm7.ChatLLM7`
- `api_key`: an optional API key for LLM7, which defaults to the `LLM7_API_KEY` environment variable

You can pass your own LLM instance from other providers:

```python
# Using OpenAI
from langchain_openai import ChatOpenAI
from headline_parser import headline_parser

llm = ChatOpenAI()
response = headline_parser("Your news headline", llm=llm)
print(response)

# Using Anthropic
from langchain_anthropic import ChatAnthropic
from headline_parser import headline_parser

llm = ChatAnthropic()
response = headline_parser("Your news headline", llm=llm)
print(response)

# Using Google
from langchain_google_genai import ChatGoogleGenerativeAI
from headline_parser import headline_parser

llm = ChatGoogleGenerativeAI()
response = headline_parser("Your news headline", llm=llm)
print(response)
```

For higher rate limits with LLM7, you can obtain a free API key by registering at https://token.llm7.io/ and pass it either as an environment variable or directly to the function:

```python
from headline_parser import headline_parser

# Via environment variable
os.environ["LLM7_API_KEY"] = "your_api_key"

# Or directly
response = headline_parser("Your news headline", api_key="your_api_key")
print(response)
```

## Contributing

Found an issue or have a feature request? Please report them on [GitHub](https://github.com/chigwell/headline-parser/issues).

## Author

Eugene Evstafev (hi@eugene.plus)