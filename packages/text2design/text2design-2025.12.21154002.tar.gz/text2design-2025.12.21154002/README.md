# text2design
[![PyPI version](https://badge.fury.io/py/text2design.svg)](https://badge.fury.io/py/text2design)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text2design)](https://pepy.tech/project/text2design)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A package for converting textual descriptions of visual design, layout, or interface concepts to structured representations or annotations.

## Overview
This package enables users to input textual descriptions of visual design, layout, or interface concepts and returns structured representations or annotations derived from the description. It leverages language model interactions coupled with pattern matching to extract key elements such as components, relationships, and attributes, facilitating tasks like generating structured design tokens, verifying design specifications, or creating markup descriptions.

## Installation
```bash
pip install text2design
```

## Usage
```python
from text2design import text2design

response = text2design(user_input="a description of the design")
```

You can also use a langchain LLM instance instead of the default `ChatLLM7` instance:
```python
from langchain_openai import ChatOpenAI
from text2design import text2design

llm = ChatOpenAI()
response = text2design(user_input="a description of the design", llm=llm)
```

### Input Parameters
- `user_input`: str, the user input text to process
- `llm`: Optional[BaseChatModel], the langchain LLM instance to use, defaults to `ChatLLM7`
- `api_key`: Optional[str], the api key for `LLM7`, can be set via environment variable `LLM7_API_KEY` or passed directly

### Supported LLMs
This package uses `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/) by default. You can pass your own LLM instance, for example:

- **OpenAI**:
```python
from langchain_openai import ChatOpenAI
from text2design import text2design

llm = ChatOpenAI()
response = text2design(user_input, llm=llm)
```

- **Anthropic**:
```python
from langchain_anthropic import ChatAnthropic
from text2design import text2design

llm = ChatAnthropic()
response = text2design(user_input, llm=llm)
```

- **Google Generative AI**:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from text2design import text2design

llm = ChatGoogleGenerativeAI()
response = text2design(user_input, llm=llm)
```

### API Key and Rate Limits
The default free tier for `LLM7` is sufficient for most use cases. For higher rate limits:
- Set your API key via environment variable `LLM7_API_KEY`
- Or pass it directly: `text2design(user_input, api_key="your_api_key")`

You can register for a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Support and Issues
For issues or feature requests, please visit: https://github....

## Author
* Eugene Evstafev (hi@eugene.plus)
* GitHub: [chigwell](https://github.com/chigwell)