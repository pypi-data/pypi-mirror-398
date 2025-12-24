# unixv4-tape-validator
[![PyPI version](https://badge.fury.io/py/unixv4-tape-validator.svg)](https://badge.fury.io/py/unixv4-tape-validator)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/unixv4-tape-validator)](https://pepy.tech/project/unixv4-tape-validator)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to interpret and validate the archival outcome of Unix V4 tapes by processing user-provided text inputs. It extracts structured data indicating success or failure along with detailed operation information, facilitating automated monitoring and validation of backup processes with language models (LLMs). This tool simplifies the verification process, allowing system administrators to quickly confirm operational status without manually parsing unstructured logs or messages.

## Installation

Install the package using pip:

```bash
pip install unixv4_tape_validator
```

## Usage

Here's an example of how to use the package in Python:

```python
from unixv4_tape_validator import unixv4_tape_validator

response = unixv4_tape_validator(
    user_input="Your tape operation output here",
    api_key="your-llm7-api-key"  # optional if LLM7_API_KEY env var is set
)
print(response)
```

## Parameters

- `user_input` (str): The text input from the user to analyze, containing tape operation details.
- `llm` (Optional[BaseChatModel]): An optional LangChain LLM instance. If not provided, the default ChatLLM7 will be instantiated.
- `api_key` (Optional[str]): Your API key for LLM7. If not provided, it can be set via the `LLM7_API_KEY` environment variable.

## LLM Support

The package uses `ChatLLM7` from `langchain_llm7` by default, which you can configure or replace with other LLMs supported by LangChain:

```python
from langchain_openai import ChatOpenAI
from unixv4_tape_validator import unixv4_tape_validator

llm = ChatOpenAI()
response = unixv4_tape_validator(user_input, llm=llm)
```

Similarly, you can use other LLMs like Anthropic or Google Generative AI:

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = unixv4_tape_validator(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = unixv4_tape_validator(user_input, llm=llm)
```

## API Key and Rate Limits

The default setup uses LLM7's free tier, which typically suffices for most use cases. For higher rate limits, you can obtain an API key free of charge by registering at [https://token.llm7.io/](https://token.llm7.io/) and set it via:

- Environment variable `LLM7_API_KEY`
- Or directly in the function call:

```python
response = unixv4_tape_validator(user_input, api_key="your_api_key")
```

## Support and Issues

For bug reports, feature requests, or other assistance, please visit the GitHub Issues page:

[https://github.com/yourusername/unixv4-tape-validator/issues](https://github.com/yourusername/unixv4-tape-validator/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)