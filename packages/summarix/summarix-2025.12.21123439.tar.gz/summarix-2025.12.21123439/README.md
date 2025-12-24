# Summarix
[![PyPI version](https://badge.fury.io/py/summarix.svg)](https://badge.fury.io/py/summarix)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/summarix)](https://pepy.tech/project/summarix)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Summarix is a Python package designed to process user-inputted text statements or stories and extract structured summaries or insights using a reliable language model with pattern matching and retries. It simplifies transforming plain text prompts into organized, actionable data by leveraging the capabilities of a pattern-aware conversation framework. This ensures consistent interpretation and mapping of user inputs into predefined data formats, avoiding ambiguities and enhancing automation in knowledge extraction or storytelling analysis.

## Features

- Uses advanced language models from langchain (by default ChatLLM7)
- Pattern matching with regex for precise output extraction
- Supports custom language model integration
- Handles retries and error management seamlessly
- Simplifies conversion of complex text inputs into structured data

## Installation

Install the package via pip:

```bash
pip install summarix
```

## Usage

Import the main function and use it with your input text:

```python
from summarix import summarix

response = summarix(user_input="Your text here")
```

### Parameters

- **user_input** *(str)*: The text statement or story to process.
- **llm** *(Optional[BaseChatModel])*: A custom langchain language model instance. Defaults to using ChatLLM7.
- **api_key** *(Optional[str])*: API key for the LLM7 service. If not provided, it will look for the environment variable `LLM7_API_KEY` or use the default free tier.

### Supporting Different Language Models

You can pass your own language model instance to utilize other providers supported by langchain, e.g., OpenAI, Anthropic, Google Generative AI.

**Example using OpenAI:**

```python
from langchain_openai import ChatOpenAI
from summarix import summarix

llm = ChatOpenAI()
response = summarix(user_input="Analyze this story", llm=llm)
```

**Example using Anthropic:**

```python
from langchain_anthropic import ChatAnthropic
from summarix import summarix

llm = ChatAnthropic()
response = summarix(user_input="Describe the scenario", llm=llm)
```

**Example using Google Generative AI:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from summarix import summarix

llm = ChatGoogleGenerativeAI()
response = summarix(user_input="Generate insights", llm=llm)
```

## Rate Limits & API Keys

The default rate limits for LLM7's free tier are sufficient for most use cases. For higher limits, you can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/) and provide it via environment variable `LLM7_API_KEY` or directly in the function call:

```python
response = summarix(user_input="Task", api_key="your_api_key")
```

## Support

For issues or feature requests, please visit the GitHub repository:

https://github.com/chigwell/summarix/issues

## Author

Eugene Evstafev

**Email:** hi@eugene.plus  
**GitHub:** [chigwell](https://github.com/chigwell)