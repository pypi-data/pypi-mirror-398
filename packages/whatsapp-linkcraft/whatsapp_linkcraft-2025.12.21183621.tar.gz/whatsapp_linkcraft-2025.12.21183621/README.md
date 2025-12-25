# WhatsApp LinkCraft
[![PyPI version](https://badge.fury.io/py/whatsapp-linkcraft.svg)](https://badge.fury.io/py/whatsapp-linkcraft)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/whatsapp-linkcraft)](https://pepy.tech/project/whatsapp-linkcraft)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


WhatsApp LinkCraft is a Python package designed to generate structured and validated WhatsApp chat links from user-provided phone numbers. It leverages language models to ensure correct formatting and automatically handle common input variations and errors, providing a clickable WhatsApp URL ready for use.

## Installation

Install the package via pip:

```bash
pip install whatsapp_linkcraft
```

## Usage

Here's a basic example of how to use the package:

```python
from whatsapp_linkcraft import whatsapp_linkcraft

# Example user input
user_input = "+1 234 567 8901"

# Generate WhatsApp link (uses default LLM)
links = whatsapp_linkcraft(user_input)
print(links)
```

You can also pass your own LLM instance if desired. The default uses `ChatLLM7` from `langchain_llm7`, which is compatible with various LLM providers.

## Custom LLM Usage

The package enables you to specify your preferred language model. For example:

### Using OpenAI's GPT

```python
from langchain_openai import ChatOpenAI
from whatsapp_linkcraft import whatsapp_linkcraft

llm = ChatOpenAI()
response = whatsapp_linkcraft(user_input, llm=llm)
```

### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from whatsapp_linkcraft import whatsapp_linkcraft

llm = ChatAnthropic()
response = whatsapp_linkcraft(user_input, llm=llm)
```

### Using Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from whatsapp_linkcraft import whatsapp_linkcraft

llm = ChatGoogleGenerativeAI()
response = whatsapp_linkcraft(user_input, llm=llm)
```

## Parameters

- **user_input** (`str`): The text input from the user containing the phone number to process.
- **llm** (`Optional[BaseChatModel]`): An instance of a language model. Defaults to `ChatLLM7`.
- **api_key** (`Optional[str]`): API key for LLM7. If not provided, the package attempts to fetch from environment variable `LLM7_API_KEY`. To use a custom key, pass it directly or set the environment variable.

## Notes

- Relies on `ChatLLM7` from `langchain_llm7` by default. You may replace it with other language model instances from [LangChain](https://docs.langchain.com/docs/).
- Default rate limits of LLM7 free tier are generally sufficient; for higher limits, provide your own API key.

## License

This project is maintained by Eugene Evstafev.

Email: hi@eugene.plus

GitHub: [chigwell](https://github.com/chigwell)

## Issues

For issues or suggestions, visit: [GitHub Issues](https://github.com/chigwell/whatsapp-linkcraft/issues)