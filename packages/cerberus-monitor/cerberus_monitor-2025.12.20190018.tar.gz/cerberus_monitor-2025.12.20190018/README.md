# Cerberus Monitor [![PyPI version](https://badge.fury.io/py/cerberus-monitor.svg)](https://pypi.org/project/cerberus-monitor/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Downloads](https://img.shields.io/pypi/dm/cerberus-monitor.svg)](https://pypi.org/project/cerberus-monitor/) [![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/eugeevstafev/)

Cerberus Monitor is a lightweight Python package designed to process and interpret network monitoring insights using advanced language models. It allows users to extract structured data from natural language prompts related to network activity analysis, leveraging the power of the langchain_llm7 library with support for flexible LLM integrations.

## Installation

```bash
pip install cerberus-monitor
```

## Usage

Here is a basic example of how to use the package:

```python
from cerberus_monitor import cerberus-monitor

user_input = "Analyze recent network traffic for anomalies."
response = cerberus_monitor(user_input)
print(response)
```

## Function Parameters

- **user_input** (`str`): The text describing the network analysis query or command.
- **llm** (`Optional[BaseChatModel]`): An optional instance of a language model from langchain (e.g., OpenAI, Anthropic). If not provided, the function defaults to using `ChatLLM7` from `langchain_llm7`.
- **api_key** (`Optional[str]`): The API key for LLM7 service. This can be set via environment variable `LLM7_API_KEY` or passed directly.

## Notes on LLM Support

This package utilizes `ChatLLM7` from `langchain_llm7` which supports multiple providers such as:

```python
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
```

For example, to use OpenAI:

```python
from langchain_openai import ChatOpenAI
from cerberus_monitor import cerberus_monitor

llm = ChatOpenAI()
response = cerberus_monitor(user_input, llm=llm)
```

Similarly, it supports other LLMs by passing their instances into the `llm` parameter.

## Rate Limits

The default free-tier rate limits for LLM7 are sufficient for most uses. For higher rate limits, set your LLM7 API key via:

- Environment variable: `LLM7_API_KEY`
- Or directly in code:

```python
response = cerberus_monitor(user_input, api_key="your_api_key")
```

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Related Resources

- [langchain_llm7 Documentation](https://pypi.org/project/langchain_llm7/)
- [GitHub Issues](https://github.com/chigwell/cerberus-monitor/issues)

## Author

**Eugene Evstafev**  
Email: [hi@eugene.plus](mailto:hi@eugene.plus)  
GitHub: [chigwell](https://github.com/chigwell)