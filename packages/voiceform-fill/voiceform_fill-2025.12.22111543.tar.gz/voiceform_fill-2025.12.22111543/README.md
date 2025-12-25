# Voiceform Fill
[![PyPI version](https://badge.fury.io/py/voiceform-fill.svg)](https://badge.fury.io/py/voiceform-fill)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/voiceform-fill)](https://pepy.tech/project/voiceform-fill)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Streamline your form-filling processes with Voiceform Fill, a package designed to convert voice input into structured, formatted text. This tool is ideal for applications where hands-free data entry is necessary, such as surveys, customer feedback forms, or any scenario where users need to quickly and accurately input information without typing.

## Installation

```bash
pip install voiceform_fill
```

## Usage

```python
from voiceform_fill import voiceform_fill

user_input = "example text"
api_key = None
llm = None

response = voiceform_fill(user_input=user_input, api_key=api_key, llm=llm)
```

**Optional Parameters**

- `user_input`: str - the user input text to process
- `llm`: Optional[BaseChatModel] - the langchain llm instance to use, if not provided the default ChatLLM7 will be used
- `api_key`: Optional[str] - the api key for llm7, if not provided the default LLM7 key will be used from the environment variable `LLM7_API_KEY` or a default key will be used

**Customizing LLM**

For advanced use cases, you can safely pass your own `llm` instance (based on https://docs.langchain.com/) by passing it like `voiceform_fill(... llm=their_llm_instance)`, for example to use the openai (https://docs.langchain.com/providers/openai):

```python
from langchain_openai import ChatOpenAI
from voiceform_fill import voiceform_fill

llm = ChatOpenAI()
response = voiceform_fill(user_input="example text", llm=llm)
```

or to use the anthropic (https://docs.langchain.com/providers/anthropic):

```python
from langchain_anthropic import ChatAnthropic
from voiceform_fill import voiceform_fill

llm = ChatAnthropic()
response = voiceform_fill(user_input="example text", llm=llm)
```

or google (https://docs.langchain.com/providers/google):

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from voiceform_fill import voiceform_fill

llm = ChatGoogleGenerativeAI()
response = voiceform_fill(user_input="example text", llm=llm)
```

**LLM Rate Limits**

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own `api_key` via environment variable `LLM7_API_KEY` or by passing it directly like `voiceform_fill(... api_key="their_api_key")`. You can get a free `api_key` by registering at https://token.llm7.io/

## Repository

This package's issues can be found at: https://github.com/chigwell/voiceform-fill

## Author

Eugene Evstafev
hi@euegne.plus