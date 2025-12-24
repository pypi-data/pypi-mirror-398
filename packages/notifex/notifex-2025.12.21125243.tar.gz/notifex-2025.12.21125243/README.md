# notifex
[![PyPI version](https://badge.fury.io/py/notifex.svg)](https://badge.fury.io/py/notifex)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/notifex)](https://pepy.tech/project/notifex)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


notifex is a Python package designed to help developers extract and structure notification content from iOS and Android devices for use with ClaudeCode. The package takes raw notification text as input and returns a standardized, machine-readable format, making it easier to consistently process and analyze notifications across different platforms.

## Installation

```bash
pip install notifex
```

## Usage

### Basic Usage

```python
from notifex import notifex

# Example with default LLM (ChatLLM7)
response = notifex("New message from John: Are we still meeting tomorrow?")
print(response)
```

### Custom LLM

You can use any LLM that's compatible with LangChain by passing a custom LLM instance:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from notifex import notifex

llm = ChatOpenAI()
response = notifex("New message from John: Are we still meeting tomorrow?", llm=llm)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from notifex import notifex

llm = ChatAnthropic()
response = notifex("New message from John: Are we still meeting tomorrow?", llm=llm)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from notifex import notifex

llm = ChatGoogleGenerativeAI()
response = notifex("New message from John: Are we still meeting tomorrow?", llm=llm)
```

### API Key Configuration

By default, notifex uses ChatLLM7 with its free tier. If you need higher rate limits, you can provide your own API key:

```python
# Via parameter
response = notifex("Your notification text", api_key="your_llm7_api_key")

# Via environment variable
import os
os.environ["LLM7_API_KEY"] = "your_llm7_api_key"
response = notifex("Your notification text")
```

You can get a free API key by registering at https://token.llm7.io/

## Parameters

- `user_input` (str): The notification text to process
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, ChatLLM7 is used by default.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, it checks the environment variable LLM7_API_KEY.

## Contributing

Found a bug or have a feature request? Please open an issue at [https://github.com/chigwell/notifex/issues](https://github.com/chigwell/notifex/issues).

## Author

Eugene Evstafev - hi@euegne.plus