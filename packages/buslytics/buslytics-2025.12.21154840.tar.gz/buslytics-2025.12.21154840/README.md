# Buslytics
[![PyPI version](https://badge.fury.io/py/buslytics.svg)](https://badge.fury.io/py/buslytics)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/buslytics)](https://pepy.tech/project/buslytics)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Buslytics is a Python package designed to process natural language user input to monitor and analyze the health and performance of message bus systems. It leverages language models to interpret queries related to message throughput, error rates, queue statuses, and system alerts, delivering structured insights that help developers and operators maintain system reliability without requiring deep technical expertise.

## Installation

Install the package via pip:

```bash
pip install buslytics
```

## Usage

Here's a basic example of how to use Buslytics:

```python
from buslytics import buslytics

response = buslytics(user_input="What is the current error rate?", api_key="your_api_key")
print(response)
```

### Parameters:
- **user_input** *(str)*: The text query input by the user for system analysis.
- **llm** *(Optional[BaseChatModel])*: An optional LangChain LLM instance. If not provided, the default ChatLLM7 from `langchain_llm7` will be used.
- **api_key** *(Optional[str])*: Your LLM7 API key. If not provided, it will be fetched from the environment variable `LLM7_API_KEY`.

### Custom LLM Usage:
You can pass your own language model instance to suit your preferred provider:

```python
from langchain_openai import ChatOpenAI
from buslytics import buslytics

llm = ChatOpenAI()
response = buslytics(user_input="Check message throughput", llm=llm)
```

Other supported models include:

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = buslytics(user_input="Check queue status", llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = buslytics(user_input="Identify system alerts", llm=llm)
```

### Notes:
- The package uses `ChatLLM7` from `langchain_llm7` by default.
- The default rate limits for the free tier of LLM7 are usually sufficient. For higher limits, supply your API key via the environment variable `LLM7_API_KEY` or directly as a parameter.
- Obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Support and Issues

Please report issues or feature requests at: [https://github.com/chigwell/buslytics/issues](https://github.com/chigwell/buslytics/issues)

## Author

**Eugene Evstafev**  
Email: hi@eugene.plus  
GitHub: [chigwell](https://github.com/chigwell)

## License

This project is licensed under the MIT License.