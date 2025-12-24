# Feedback Analyzer Mod
[![PyPI version](https://badge.fury.io/py/feedback-analyzer-mod.svg)](https://badge.fury.io/py/feedback-analyzer-mod)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/feedback-analyzer-mod)](https://pepy.tech/project/feedback-analyzer-mod)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to analyze and structure user-submitted text, specifically focusing on community feedback and moderation. This tool leverages the capabilities of `llmatch-messages` to process and extract meaningful insights from user inputs, such as forum posts, comments, or feedback forms. By using pattern matching and retry logic, the package ensures that the extracted data is consistent and formatted correctly, making it easier for moderators to review and respond to user feedback.

## Features

- **Pattern Matching**: Extracts structured data from unstructured user inputs.
- **Retry Logic**: Ensures consistent and reliable data extraction.
- **Flexible LLM Integration**: Supports various LLM providers, including LLM7, OpenAI, Anthropic, and Google.
- **Easy Integration**: Simple API for seamless integration into existing workflows.

## Installation

```bash
pip install feedback_analyzer_mod
```

## Usage

### Basic Usage

```python
from feedback_analyzer_mod import feedback_analyzer_mod

user_input = "Your user input text here"
response = feedback_analyzer_mod(user_input)
print(response)
```

### Using a Custom LLM

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from feedback_analyzer_mod import feedback_analyzer_mod

llm = ChatOpenAI()
response = feedback_analyzer_mod(user_input, llm=llm)
print(response)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from feedback_analyzer_mod import feedback_analyzer_mod

llm = ChatAnthropic()
response = feedback_analyzer_mod(user_input, llm=llm)
print(response)
```

#### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from feedback_analyzer_mod import feedback_analyzer_mod

llm = ChatGoogleGenerativeAI()
response = feedback_analyzer_mod(user_input, llm=llm)
print(response)
```

## Parameters

- **user_input** (str): The user input text to process.
- **llm** (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- **api_key** (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

The package uses `ChatLLM7` from `langchain_llm7` by default. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter.

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)

## Issues

For any issues or suggestions, please open an issue on [GitHub](https://github.com/chigwell/feedback-analyzer-mod/issues).