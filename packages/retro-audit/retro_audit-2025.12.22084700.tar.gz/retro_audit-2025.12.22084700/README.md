# retro-audit
[![PyPI version](https://badge.fury.io/py/retro-audit.svg)](https://badge.fury.io/py/retro-audit)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/retro-audit)](https://pepy.tech/project/retro-audit)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


retro-audit is a Python package designed to facilitate the evaluation and improvement of retro gaming content. By analyzing user descriptions of their projects, it provides structured feedback to enhance authenticity, trustworthiness, and engagement. The tool utilizes advanced language models to generate clear, actionable suggestions, making it an invaluable resource for developers and enthusiasts aiming to create standout retro gaming sites.

## Installation

Install the package via pip:

```bash
pip install retro_audit
```

## Usage

Here is a simple example of how to use the package in Python:

```python
from retro_audit import retro_audit

# User input describing their retro gaming project
user_input = "I am building a nostalgic arcade website with old-school design and authentic gameplay reviews."

# Calling the retro_audit function with default language model
feedback = retro_audit(user_input)

print(feedback)
```

## Parameters

- `user_input` (str): The description of your retro gaming project or content.
- `llm` (Optional[BaseChatModel]): An optional language model instance from langchain. If not provided, the default will be used.
- `api_key` (Optional[str]): API key for the LLM service. If not provided, it attempts to use the environment variable `LLM7_API_KEY`. You can also set this environment variable directly.

## Underlying Technology

This package leverages `ChatLLM7` from `langchain_llm7` (available on PyPI: [https://pypi.org/project/langchain_llm7/](https://pypi.org/project/langchain_llm7/)). It allows flexibility for developers to supply their own language models, such as OpenAI, Anthropic, or Google models, by passing a different `llm` instance as shown below:

```python
from langchain_openai import ChatOpenAI
from retro_audit import retro_audit

llm = ChatOpenAI()
response = retro_audit(user_input, llm=llm)
```

Other examples:

```python
from langchain_anthropic import ChatAnthropic
from retro_audit import retro_audit

llm = ChatAnthropic()
response = retro_audit(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from retro_audit import retro_audit

llm = ChatGoogleGenerativeAI()
response = retro_audit(user_input, llm=llm)
```

## Rate Limits

The default setup uses the free tier of LLM7, which is suitable for most use cases. For higher rate limits, you can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/) and set it via environment variable `LLM7_API_KEY` or directly in your code:

```python
response = retro_audit(user_input, api_key="your_api_key")
```

## Support and Issues

For support or to report issues, please open a ticket at:  
[https://github.com/chigwell/retro-audit/issues](https://github.com/chigwell/retro-audit/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)