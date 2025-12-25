# Text-Digestor
[![PyPI version](https://badge.fury.io/py/text-digestor.svg)](https://badge.fury.io/py/text-digestor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/text-digestor)](https://pepy.tech/project/text-digestor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Transform raw text into a clean, readable article format with Text-Digestor.

## Overview

Text-Digestor is a package that extracts the main content from unstructured text, such as web content or documents, and processes it to remove unnecessary elements like advertisements, navigation links, and sidebars. It focuses on preserving the core narrative, making it ideal for applications that require distraction-free reading experiences.

## Features

- Extracts main content from unstructured text
- Removes unnecessary elements like advertisements, navigation links, and sidebars
- Preserves core narrative
- Well-organized and easy-to-consume output

## Installation

```bash
pip install text_digestor
```

## Example Usage

```python
from text_digestor import text_digestor

user_input = "Unstructured text to process..."
response = text_digestor(user_input)
print(response)
```

## Input Parameters

- `user_input`: `str`: the user input text to process
- `llm`: `Optional[BaseChatModel]`: the Langchain LLM instance to use, defaults to `ChatLLM7` from `langchain_llm7` if not provided
- `api_key`: `Optional[str]`: the API key for LLM7, defaults to an empty string (`api_key is None`) if not provided

Note that you can safely pass your own LLM instance if you want to use another LLM. For example, to use OpenAI's LLM, you can pass it like this:
```python
from langchain_openai import ChatOpenAI
from text_digestor import text_digestor

llm = ChatOpenAI()
response = text_digestor(user_input, llm=llm)
```
Similarly, you can use Anthropic's LLM:
```python
from langchain_anthropic import ChatAnthropic
from text_digestor import text_digestor

llm = ChatAnthropic()
response = text_digestor(user_input, llm=llm)
```
Or Google's LLM:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from text_digestor import text_digestor

llm = ChatGoogleGenerativeAI()
response = text_digestor(user_input, llm=llm)
```
## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or directly like this:
```python
response = text_digestor(user_input, api_key="your_api_key")
```
You can get a free API key by registering at [Token.LLM7.IO](https://token.llm7.io/)

## Issues

Report any issues to our [GitHub Issues Page](https://github.com/chigwell/text-digestor)

## Author

Eugene Evstafev
[eugene.evstafev@hi@euegne.plus](mailto:hi@eugene.plus)

## License

MIT License