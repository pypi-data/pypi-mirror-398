# Philosim
[![PyPI version](https://badge.fury.io/py/philosim.svg)](https://badge.fury.io/py/philosim)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/philosim)](https://pepy.tech/project/philosim)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Philosim is a Python package that leverages the power of llmatch-messages to provide structured insights into complex philosophical and scientific topics, such as the simulation hypothesis.

## Installation

Installation is simple:
```
pip install philosim
```
## Usage

The main function `philosim` takes three parameters:

- `user_input`: a string containing the topic or question you want to explore.
- `llm`: an optional parameter for the LangChain LLM instance to use. If not provided, the package will use the `ChatLLM7` instance from `langchain_llm7` by default.
- `api_key`: an optional parameter for the LLM7 API key. If not provided, the package will use the `LLM7_API_KEY` environment variable or the default free tier API key.

```python
from philosim import philosim

# Using the default llm
response = philosim(user_input)

# Using a custom llm instance (e.g. openai)
from langchain_openai import ChatOpenAI
llm = ChatOpenAI()
response = philosim(user_input, llm=llm)

# Using a custom llm instance (e.g. anthropic)
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = philosim(user_input, llm=llm)

# Using a custom llm instance (e.g. google)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = philosim(user_input, llm=llm)

# Using a custom llm7 api key
response = philosim(user_input, api_key="your_api_key")
```
## Note on LLM Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly like `philosim(user_input, api_key="your_api_key")`. You can get a free API key by registering at https://token.llm7.io/.

## Issues

To report any issues or request features, please visit our GitHub repository: <https://github.com/chigwell/philosim/issues>

## Author

Philosim was created by Eugene Evstafev (<hi@eugene.plus>)

## License

Philosim is released under the [MIT License](https://opensource.org/licenses/MIT).

## Changelog

[Add changelog here]