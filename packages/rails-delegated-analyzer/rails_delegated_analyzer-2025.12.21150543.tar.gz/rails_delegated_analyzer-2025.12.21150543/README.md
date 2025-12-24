# Rails Delegated Analyzer
[![PyPI version](https://badge.fury.io/py/rails-delegated-analyzer.svg)](https://badge.fury.io/py/rails-delegated-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/rails-delegated-analyzer)](https://pepy.tech/project/rails-delegated-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Rails Delegated Analyzer is a Python package designed to help developers understand and apply the Rails Delegated Type pattern. It analyzes text-based descriptions of database relationships or use cases and provides structured explanations for implementing delegated types in Rails applications.

## Features

- Analyzes user input about data models or scenarios
- Provides structured explanations for implementing delegated types
- Assists in designing polymorphic-like structures in Rails applications
- Supports custom LLM instances for flexible usage

## Installation

```bash
pip install rails_delegated_analyzer
```

## Usage

### Basic Usage

```python
from rails_delegated_analyzer import rails_delegated_analyzer

user_input = "Describe your data model or scenario here."
response = rails_delegated_analyzer(user_input)
print(response)
```

### Using a Custom LLM Instance

The package uses `ChatLLM7` from `langchain_llm7` by default. However, you can safely pass your own LLM instance if you want to use another LLM.

#### Example with OpenAI

```python
from langchain_openai import ChatOpenAI
from rails_delegated_analyzer import rails_delegated_analyzer

llm = ChatOpenAI()
response = rails_delegated_analyzer(user_input, llm=llm)
print(response)
```

#### Example with Anthropic

```python
from langchain_anthropic import ChatAnthropic
from rails_delegated_analyzer import rails_delegated_analyzer

llm = ChatAnthropic()
response = rails_delegated_analyzer(user_input, llm=llm)
print(response)
```

#### Example with Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from rails_delegated_analyzer import rails_delegated_analyzer

llm = ChatGoogleGenerativeAI()
response = rails_delegated_analyzer(user_input, llm=llm)
print(response)
```

### Using a Custom API Key

If you want to use a custom API key for LLM7, you can pass it directly or via an environment variable.

#### Using Environment Variable

```bash
export LLM7_API_KEY="your_api_key"
```

#### Passing API Key Directly

```python
from rails_delegated_analyzer import rails_delegated_analyzer

user_input = "Describe your data model or scenario here."
response = rails_delegated_analyzer(user_input, api_key="your_api_key")
print(response)
```

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/rails-delegated-analyzer/issues).

## Author

- **Eugene Evstafev** - [chigwell](https://github.com/chigwell)
- **Email**: hi@eugene.plus