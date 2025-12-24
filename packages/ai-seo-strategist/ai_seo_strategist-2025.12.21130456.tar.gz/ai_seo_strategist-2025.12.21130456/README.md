# AI SEO Strategist
[![PyPI version](https://badge.fury.io/py/ai-seo-strategist.svg)](https://badge.fury.io/py/ai-seo-strategist)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ai-seo-strategist)](https://pepy.tech/project/ai-seo-strategist)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


AI SEO Strategist is a Python package designed to streamline the extraction and organization of AI-driven SEO strategies from user inputs. This tool helps founders and marketers quickly access practical SEO tactics tailored to their specific challenges or goals, enabling efficient planning and implementation.

## Features

- **Structured Output**: Generates a categorized list of actionable SEO strategies.
- **Customizable LLM**: Uses `ChatLLM7` by default but can be configured with any `BaseChatModel` from LangChain.
- **Consistent Formatting**: Ensures clear and consistent output for easy integration into workflows and documents.
- **Flexible API Key Management**: Supports API key via environment variable or direct input.

## Installation

```bash
pip install ai_seo_strategist
```

## Usage

### Basic Usage

```python
from ai_seo_strategist import ai_seo_strategist

user_input = "Improve SEO for my e-commerce website"
strategies = ai_seo_strategist(user_input)
print(strategies)
```

### Using a Custom LLM

You can use any LLM compatible with LangChain's `BaseChatModel`. Here are examples using different LLMs:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from ai_seo_strategist import ai_seo_strategist

llm = ChatOpenAI()
response = ai_seo_strategist(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from ai_seo_strategist import ai_seo_strategist

llm = ChatAnthropic()
response = ai_seo_strategist(user_input, llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from ai_seo_strategist import ai_seo_strategist

llm = ChatGoogleGenerativeAI()
response = ai_seo_strategist(user_input, llm=llm)
print(response)
```

### Using an API Key

You can pass an API key directly or use an environment variable.

#### Using Environment Variable

```bash
export LLM7_API_KEY="your_api_key"
```

#### Passing API Key Directly

```python
from ai_seo_strategist import ai_seo_strategist

user_input = "Improve SEO for my e-commerce website"
strategies = ai_seo_strategist(user_input, api_key="your_api_key")
print(strategies)
```

## Parameters

- **user_input** (str): The user input text to process.
- **llm** (Optional[BaseChatModel]): The LangChain LLM instance to use. Defaults to `ChatLLM7`.
- **api_key** (Optional[str]): The API key for LLM7. If not provided, it will use the environment variable `LLM7_API_KEY`.

## Rate Limits

The default rate limits for LLM7's free tier are sufficient for most use cases. If you need higher rate limits, you can obtain a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

For any issues or suggestions, please open an issue on [GitHub](https://github.com/chigwell/ai-seo-strategist).

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)