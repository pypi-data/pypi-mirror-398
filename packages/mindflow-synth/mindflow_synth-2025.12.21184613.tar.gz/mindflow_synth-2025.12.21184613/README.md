# MindFlow Synth
[![PyPI version](https://badge.fury.io/py/mindflow-synth.svg)](https://badge.fury.io/py/mindflow-synth)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/mindflow-synth)](https://pepy.tech/project/mindflow-synth)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Package designed to extract and structure key insights from text about cognitive processes, such as deep focus and flow states.

## Overview
The MindFlow Synth package takes text input describing psychological or neurological concepts and returns a structured summary that highlights the main principles, triggers, and benefits of achieving deep focus. It leverages advanced language models to parse and organize information, providing a reliable and repeatable way to distill complex ideas into actionable insights.

## Installation
```
pip install mindflow_synth
```

## Usage
```python
from mindflow_synth import mindflow_synth

user_input = "Text about cognitive processes..."
response = mindflow_synth(user_input)
print(response)
```

## Function Signature
```python
def mindflow_synth(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]
```
- `user_input`: str - the user input text to process
- `api_key`: Optional[str] - the api key for llm7, if not provided the default ChatLLM7 will be used
- `llm`: Optional[BaseChatModel] - the langchain llm instance to use, if not provided the default ChatLLM7 will be used

## Default LLM
The package uses the ChatLLM7 from `langchain_llm7` by default. You can safely pass your own `llm` instance (based on `langchain`) if you want to use another LLM, for example:
```python
from langchain_openai import ChatOpenAI
from mindflow_synth import mindflow_synth
llm = ChatOpenAI()
response = mindflow_synth(... llm=llm)
```
or for example to use the anthropic:
```python
from langchain_anthropic import ChatAnthropic
from mindflow_synth import mindflow_synth
llm = ChatAnthropic()
response = mindflow_synth(... llm=llm)
```
or google:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from mindflow_synth import mindflow_synth
llm = ChatGoogleGenerativeAI()
response = mindflow_synth(... llm=llm)
```

## LLM7 Rate Limits
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly like `mindflow_synth(... api_key="your_api_key")`. You can get a free API key by registering at https://token.llm7.io/

## Issues
For any issues or feature requests, please submit a pull request to https://github.com/chigwell/mindflow-synth

## Author
Eugene Evstafev (hi@euegne.plus)