# Preact Codegen
[![PyPI version](https://badge.fury.io/py/preact-codegen.svg)](https://badge.fury.io/py/preact-codegen)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/preact-codegen)](https://pepy.tech/project/preact-codegen)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

Preact Codegen is a package that helps developers quickly set up Preact applications without needing a complex build configuration. Users can describe their application requirements in plain text, including desired routing and signal management features. The package processes this input to generate a structured, ready-to-use Preact application code snippet.

## Key Features

- Generate Preact application code from user input in plain text
- Supports routing and signal management features
- Easy to integrate and expand
- Simple and fast setup

## Installation

```bash
pip install preact_codegen
```

## Usage

```python
from preact_codegen import preact_codegen

user_input = "Describe your Preact application requirements here..."
api_key = "your_api_key_here"  # Optional, if not provided, the default LLM7 will be used

response = preact_codegen(
    user_input=user_input,
    api_key=api_key,
)
print(response)
```

## Parameters

- `user_input`: The user input text to process (type: `str`)
- `llm`: The `langchain` LLM instance to use (optional, type: `Optional[BaseChatModel]`), defaults to `ChatLLM7` from `langchain_llm7`
- `api_key`: The API key for LLM7 (optional, type: `Optional[str]`), defaults to `os.getenv("LLM7_API_KEY")` or `None`

## Notes

- The package uses `ChatLLM7` from `langchain_llm7` by default. You can safely pass your own LLM instance (based on `langchain`) if you want to use another LLM.

  Example for `ChatOpenAI`:

  ```python
  from langchain_openai import ChatOpenAI
  from preact_codegen import preact_codegen

  llm = ChatOpenAI()
  response = preact_codegen(
      user_input=user_input,
      llm=llm,
  )
  ```

  Example for `ChatAnthropic`:

  ```python
  from langchain_anthropic import ChatAnthropic
  from preact_codegen import preact_codegen

  llm = ChatAnthropic()
  response = preact_codegen(
      user_input=user_input,
      llm=llm,
  )
  ```

  Example for `ChatGoogleGenerativeAI`:

  ```python
  from langchain_google_genai import ChatGoogleGenerativeAI
  from preact_codegen import preact_codegen

  llm = ChatGoogleGenerativeAI()
  response = preact_codegen(
      user_input=user_input,
      llm=llm,
  )
  ```

- The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own `API_KEY` via environment variable `LLM7_API_KEY` or directly like `preact_codegen(api_key="your_api_key")`.
- You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Links

- GitHub issues: [GitHub Issues](https://github.com/chigwell/preact-codegen/issues)
- Author name: Eugene Evstafev
- Author email: hi@euegne.plus