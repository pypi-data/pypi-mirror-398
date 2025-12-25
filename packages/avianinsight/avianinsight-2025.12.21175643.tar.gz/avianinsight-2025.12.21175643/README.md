# Avian Insight
[![PyPI version](https://badge.fury.io/py/avianinsight.svg)](https://badge.fury.io/py/avianinsight)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/avianinsight)](https://pepy.tech/project/avianinsight)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

A package that extracts insights on bird behavior from text descriptions using pattern-matched LLM responses.

## Installation
```bash
pip install avianinsight
```

## Usage
```python
from avianinsight import avianinsight

response = avianinsight(user_input, api_key="your_api_key", llm=your_llm_instance)
```

## Parameters
- `user_input`: str - the user input text to process
- `llm`: Optional[BaseChatModel] - the langchain llm instance to use, defaults to ChatLLM7
- `api_key`: Optional[str] - the api key for llm7, defaults to LLM7_API_KEY environment variable or "None"

## Using alternative LLM instances
You can pass your own llm instance (based on [https://docs.langchain.com/](https://docs.langchain.com/)) by passing it like `avianinsight(user_input, llm=their_llm_instance)`, for example:
```python
from langchain_openai import ChatOpenAI from avianinsight import avianinsight
llm = ChatOpenAI()
response = avianinsight(user_input, llm=llm)
```
```python
from langchain_anthropic import ChatAnthropic from avianinsight import avianinsight
llm = ChatAnthropic()
response = avianinsight(user_input, llm=llm)
```
```python
from langchain_google_genai import ChatGoogleGenerativeAI from avianinsight import avianinsight
llm = ChatGoogleGenerativeAI()
response = avianinsight(user_input, llm=llm)
```
## API Key Limitations
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own api_key via environment variable LLM7_API_KEY or via passing it directly like `avianinsight(user_input, api_key="your_api_key"`.

## Contributing
If you encounter any issues or have suggestions for improvement, please report them on the GitHub issues page: https://github.com/chigwell/avianinsight

## Author
* **Eugene Evstafev** - hi@euegne.plus
* **GitHub:** chigwell