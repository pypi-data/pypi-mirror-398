# LLM Test Helper (`llmtestr`)
[![PyPI version](https://badge.fury.io/py/llmtestr.svg)](https://badge.fury.io/py/llmtestr)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/llmtestr)](https://pepy.tech/project/llmtestr)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`llmtestr` is a Python package designed to assist developers in integration-testing AI and Language Model applications by validating structured outputs. It provides a simple interface to send a prompt or test scenario to an LLM, then verifies that the response matches predefined patterns using pattern matching mechanisms. This helps ensure that your LLM outputs adhere to expected formats such as code snippets, JSON structures, or tagged responses, making it easier to catch formatting errors, regressions, or inconsistencies during development and testing.

## Installation

Install the package via pip:

```bash
pip install llmtestr
```

## Usage

Here's a basic example of how to use `llmtestr` in your Python code:

```python
from llmtestr import llmtestr

response = llmtestr(user_input="Your test prompt here")
print(response)
```

## Function Parameters

- `user_input` (*str*): The prompt or test scenario you want to evaluate.
- `llm` (*Optional[BaseChatModel]*): An optional `langchain` LLM instance to use. If not provided, `llmtestr` defaults to using `ChatLLM7`.
- `api_key` (*Optional[str]*): Your API key for `LLM7`. If not provided, it will attempt to fetch from the environment variable `LLM7_API_KEY`.

## Underlying LLM

By default, `llmtestr` uses the `ChatLLM7` class from `langchain_llm7`, which you can find on PyPI: [langchain_llm7](https://pypi.org/project/langchain-llm7/). You can also pass your custom LLM instance based on the `langchain` interface for different providers like OpenAI, Anthropic, Google, etc.

### Examples:

**Using OpenAI:**

```python
from langchain_openai import ChatOpenAI
from llmtestr import llmtestr

llm = ChatOpenAI()
response = llmtestr(user_input="Test prompt", llm=llm)
```

**Using Anthropic:**

```python
from langchain_anthropic import ChatAnthropic
from llmtestr import llmtestr

llm = ChatAnthropic()
response = llmtestr(user_input="Test prompt", llm=llm)
```

**Using Google Generative AI:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from llmtestr import llmtestr

llm = ChatGoogleGenerativeAI()
response = llmtestr(user_input="Test prompt", llm=llm)
```

## Rate Limits & API Keys

The default free tier for LLM7 provides sufficient rate limits for most development needs. To get higher limits, you can:

- Set the environment variable `LLM7_API_KEY`.
- Pass your API key directly:

```python
response = llmtestr(user_input="Test prompt", api_key="your_api_key")
```

Register for a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Support & Issues

For issues, bugs, or feature requests, please visit the GitHub repo issues page: [https://github.com/chigwell/llmtestr/issues](https://github.com/chigwell/llmtestr/issues).

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)