# Lawhead Extractor
[![PyPI version](https://badge.fury.io/py/lawhead-extractor.svg)](https://badge.fury.io/py/lawhead-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/lawhead-extractor)](https://pepy.tech/project/lawhead-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

**Extract structured information from legal case headlines**

The Lawhead Extractor is a Python package that processes legal case headlines and extracts structured information such as the parties involved, the type of claim, and the outcome. It uses a Large Language Model (LLM) to analyze the text input and returns a consistent, formatted response with key details, ensuring accuracy through pattern matching and retries.

## Installation

```bash
pip install lawhead_extractor
```

## Usage
```python
from lawhead_extractor import lawhead_extractor
import os

# default usage
response = lawhead_extractor(user_input="an example user input text")
print(response)

# usage with custom LLM instance (e.g. OpenAI)
from langchain_openai import ChatOpenAI
from lawhead_extractor import lawhead_extractor
llm = ChatOpenAI()
response = lawhead_extractor(user_input="user input text", llm=llm)

# usage with custom LLM instance (e.g. Anthropic)
from langchain_anthropic import ChatAnthropic
from lawhead_extractor import lawhead_extractor
llm = ChatAnthropic()
response = lawhead_extractor(user_input="user input text", llm=llm)

# usage with custom LLM instance (e.g. Google Generative AI)
from langchain_google_genai import ChatGoogleGenerativeAI
from lawhead_extractor import lawhead_extractor
llm = ChatGoogleGenerativeAI()
response = lawhead_extractor(user_input="user input text", llm=llm)
```

## Input Parameters
- `user_input`: `str`: the user input text to process
- `llm`: `Optional[BaseChatModel]`: the langchain LLM instance to use, if not provided, the default `ChatLLM7` will be used.
- `api_key`: `Optional[str]`: the API key for LLM7, if not provided, the default rate limits for LLM7 free tier will be used.

By default, the package uses the `ChatLLM7` from `langchain_llm7 <https://pypi.org/project/langchain_llm7/>`. Developers can safely pass their own LLM instance (based on `https://docs.langchain.com/docs/llm/how-to-use-another-llm`) if they want to use another LLM, via passing it like `lawhead_extractor(llm=their_llm_instance)`, for example to use the OpenAI `https://docs.langchain.com/docs/openai/how-to-use-openai`, Anthropic `https://docs.langchain.com/docs/anthropic/how-to-use-anthropic`, or Google Generative AI `https://docs.langchain.com/docs/google/generative-ai/how-to-use-google-generative-ai`.

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If developers want higher rate limits for LLM7, they can pass their own API key via environment variable `LLM7_API_KEY` or via passing it directly like `lawhead_extractor(api_key="their_api_key")`. Developers can get a free API key by registering at `https://token.llm7.io/`.

## Issues
Find and report any issues with the package on our GitHub issues page: https://github.com/chigwell/lawhead_extractor

## Author
The Lawhead Extractor package was created by Eugene Evstafev and is maintained by Eugene Evstafev.

Contact the author at: hi@eugene.plus

Follow Chigwell on GitHub at: https://github.com/chigwell