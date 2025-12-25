# whatsapp-linkify
[![PyPI version](https://badge.fury.io/py/whatsapp-linkify.svg)](https://badge.fury.io/py/whatsapp-linkify)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/whatsapp-linkify)](https://pepy.tech/project/whatsapp-linkify)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


whatsapp-linkify is a Python package that transforms phone numbers into direct WhatsApp chat links. It allows users to input a phone number or text containing phone numbers, and processes this input to generate structured WhatsApp chat URLs. This is especially useful for businesses, customer support teams, or anyone needing quick access to WhatsApp chats without manually formatting links.

## Installation

Install the package via pip:

```bash
pip install whatsapp_linkify
```

## Usage

Here's a basic example of how to use the package:

```python
from whatsapp_linkify import whatsapp_linkify

results = whatsapp_linkify(
    user_input="Call me at +1234567890 or +19876543210.",
)
print(results)
```

## Parameters

- **user_input**: `str`  
  The input text containing phone numbers to process.

- **llm**: `Optional[BaseChatModel]`  
  An optional language model instance to use. If not provided, the default `ChatLLM7` from `langchain_llm7` is used.

- **api_key**: `Optional[str]`  
  An optional API key for LLM7. If not provided, it will be fetched from the environment variable `LLM7_API_KEY`.

## LLM Compatibility and Customization

The package uses `ChatLLM7` from the `langchain_llm7` package (https://pypi.org/project/langchain-llm7/).  
Developers can pass their own language model instances to `whatsapp_linkify`, supporting models such as:

- OpenAI (via `langchain_openai.ChatOpenAI`)  
  ```python
  from langchain_openai import ChatOpenAI
  from whatsapp_linkify import whatsapp_linkify
  
  llm = ChatOpenAI()
  response = whatsapp_linkify(user_input, llm=llm)
  ```

- Anthropic (via `langchain_anthropic.ChatAnthropic`)  
  ```python
  from langchain_anthropic import ChatAnthropic
  from whatsapp_linkify import whatsapp_linkify
  
  llm = ChatAnthropic()
  response = whatsapp_linkify(user_input, llm=llm)
  ```

- Google Generative AI (via `langchain_google_genai.ChatGoogleGenerativeAI`)  
  ```python
  from langchain_google_genai import ChatGoogleGenerativeAI
  from whatsapp_linkify import whatsapp_linkify
  
  llm = ChatGoogleGenerativeAI()
  response = whatsapp_linkify(user_input, llm=llm)
  ```

The default rate limits for LLM7’s free tier are sufficient for most use cases. For higher limits, users can obtain an API key from https://token.llm7.io/ and pass it via the `api_key` parameter or environment variable.

## License

This project is maintained by Eugene Evstafev.  
Author email: hi@euegne.plus  
GitHub profile: [chigwell](https://github.com/chigwell)  

## Issues

For issues and feature requests, please visit:  
https://github.com/chigwell/whatsapp-linkify/issues