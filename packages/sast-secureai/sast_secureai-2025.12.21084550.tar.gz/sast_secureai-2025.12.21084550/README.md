# sast-secureai
[![PyPI version](https://badge.fury.io/py/sast-secureai.svg)](https://badge.fury.io/py/sast-secureai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/sast-secureai)](https://pepy.tech/project/sast-secureai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


sast-secureai is a Python package that automates software security analysis and testing (SAST) by leveraging AI-powered language models. It allows users to input code snippets or textual descriptions of software functionality and returns a structured report highlighting potential security vulnerabilities, threats, or risks.

## Installation

You can install the package using pip:

```bash
pip install sast_secureai
```

## Usage

Here's an example of how to use the package in Python:

```python
from sast_secureai import sast_secureai

user_input = "Your code snippet or description here..."

response = sast_secureai(user_input)
print(response)
```

## Function Parameters

- `user_input` (str): The code snippet or description of functionality to analyze.
- `llm` (Optional[BaseChatModel]): An optional LangChain language model instance. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): An optional API key for LLM7. If not provided, the package attempts to retrieve it from the environment variable `LLM7_API_KEY`.

## Custom LLM Support

You can pass your own language model instance to suit your preferred LLM provider by importing and initializing it accordingly. Supported examples include:

```python
from langchain_openai import ChatOpenAI
from sast_secureai import sast_secureai

llm = ChatOpenAI()
response = sast_secureai(user_input, llm=llm)
```

or

```python
from langchain_anthropic import ChatAnthropic
from sast_secureai import sast_secureai

llm = ChatAnthropic()
response = sast_secureai(user_input, llm=llm)
```

or

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from sast_secureai import sast_secureai

llm = ChatGoogleGenerativeAI()
response = sast_secureai(user_input, llm=llm)
```

The default LLM used is ChatLLM7 from `langchain_llm7`, which can be configured with an API key. Obtain your free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Rate Limits

The included default rate limits for LLM7's free tier are sufficient for most use cases. For higher rate limits, set your API key via the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = sast_secureai(user_input, api_key="your_api_key")
```

## Support and Issues

For issues or feature requests, please use the GitHub issues page:

[https://github.com/chigwell/sast-secureai/issues](https://github.com/chigwell/sast-secureai/issues)

## Author

Eugene Evstafev  
Email: hi@eugene.plus  
GitHub: [chigwell](https://github.com/chigwell)