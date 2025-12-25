# finclaimvalid
[![PyPI version](https://badge.fury.io/py/finclaimvalid.svg)](https://badge.fury.io/py/finclaimvalid)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/finclaimvalid)](https://pepy.tech/project/finclaimvalid)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


finclaimvalid is a Python package that helps you assess the validity of financial or investment claims through natural language analysis. It interprets user queries and provides structured, concise responses based on historical data patterns. This tool is especially useful for financial advisors, educational platforms, or individual investors seeking quick, reliable insights without manual data searches.

## Installation

Install the package via pip:

```bash
pip install finclaimvalid
```

## Usage Example

Here's a basic example demonstrating how to use finclaimvalid with your own language model:

```python
from finclaimvalid import finclaimvalid

# Using the default LLM7 model
response = finclaimvalid(user_input="Is the recent claim about stock growth valid?")

# Using a custom language model, e.g., OpenAI's ChatOpenAI
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
response = finclaimvalid(user_input="Is the recent claim about stock growth valid?", llm=llm)
```

### Parameters

- **user_input** *(str)*: The text query about the financial claim.
- **llm** *(Optional[BaseChatModel])*: An optional language model instance from langchain. If not provided, the default ChatLLM7 will be used.
- **api_key** *(Optional[str])*: Your API key for LLM7 services. If not provided, the package will look for the environment variable `LLM7_API_KEY`. You can obtain a free key at [https://token.llm7.io/](https://token.llm7.io/).

### Supported Language Models

- **ChatLLM7** (default), from `langchain_llm7`

You can also pass other models, such as:

```python
from langchain_anthropic import ChatAnthropic
from finclaimvalid import finclaimvalid

llm = ChatAnthropic()
response = finclaimvalid(user_input="Check the validity of this claim.", llm=llm)
```

## Notes

- The package adapts to various LLMs by accepting any compatible language model instance.
- Rate limits typically match the free tier of LLM7 but can be increased by applying for a higher quota using your API key.
- Your API key can be set via environment variable or directly passed as an argument.

## License

This project is licensed under the MIT License.

## Support

For issues or feature requests, please visit the GitHub issues page:  
[https://github.com/.../issues](https://github.com/.../issues)

## Author

- **Eugene Evstafev**  
  Email: hi@eugene.plus  
  GitHub: [@chigwell](https://github.com/chigwell)