# Heritage Insight Package
[![PyPI version](https://badge.fury.io/py/heritage-insight.svg)](https://badge.fury.io/py/heritage-insight)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/heritage-insight)](https://pepy.tech/project/heritage-insight)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

leveraging pattern matching with language models to generate structured summaries and insights from user-provided historical or cultural texts.

## Overview
A new package that accepts textual inputs related to specific topics or events and returns organized, key information such as summaries, timelines, or thematic breakdowns.

## Installation
```bash
pip install heritage_insight
```

## Usage
```python
from heritage_insight import heritage_insight

user_input = "Input text here"
response = heritage_insight(user_input, verbose=False)
```

## Example usage with specific LLMs
```python
from heritage_insight import heritage_insight
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

openai_response = heritage_insight(user_input, llm=ChatOpenAI())
anthropic_response = heritage_insight(user_input, llm=ChatAnthropic())
google_response = heritage_insight(user_input, llm=ChatGoogleGenerativeAI())
```

## Configuration
- `user_input`: str: the user input text to process
- `llm`: Optional[BaseChatModel]: the langchain llm instance to use, defaults to ChatLLM7
- `api_key`: Optional[str]: the api key for llm7, defaults to LLM7_API_KEY environment variable or LLM7 free tier limits

## Using custom LLMs
You can safely pass your own llm instance (based on https://docs.langchain.dev/) if you want to use another LLM, via passing it like `heritage_insight(user_input, llm=your_llm_instance)`.

## LLM7 API Key
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own `api_key` via environment variable `LLM7_API_KEY` or via passing it directly like `heritage_insight(user_input, api_key="your_api_key")`. You can get a free api key by registering at https://token.llm7.io/

## Support and Issues
Report issues and provide feedback at https://github.com/chigwell/heritage-insight

## Author
Eugene Evstafev (hi@eugene.plus)