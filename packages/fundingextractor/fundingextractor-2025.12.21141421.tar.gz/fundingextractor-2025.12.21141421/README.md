# FundingExtractor
[![PyPI version](https://badge.fury.io/py/fundingextractor.svg)](https://badge.fury.io/py/fundingextractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/fundingextractor)](https://pepy.tech/project/fundingextractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


FundingExtractor is a Python package designed to process news headlines and extract structured information about company funding events. Using pattern matching, it ensures consistent and accurate data extraction from text inputs, capturing details such as startup names, valuation amounts, and funding rounds.

## Installation

```bash
pip install fundingextractor
```

## Usage Example

```python
from fundingextractor import fundingextractor

# Example user input
user_input = "Tech startup ABC raised $50M in Series A funding."

# Call the function with default LLM
results = fundingextractor(user_input)
print(results)
```

## Parameters

- **user_input**: `str`  
  The input text to process, such as news headlines or reports.

- **llm**: `Optional[BaseChatModel]`  
  An optional LangChain LLM instance. Defaults to using `ChatLLM7` from `langchain_llm7`.

- **api_key**: `Optional[str]`  
  API key for the LLM service. If not provided, the package will attempt to use the `LLM7_API_KEY` environment variable.

## Supported LLMs

The package uses `ChatLLM7` from `langchain_llm7` by default. You can also pass your own LLM instance to leverage different providers, such as:

- OpenAI

```python
from langchain_openai import ChatOpenAI
from fundingextractor import fundingextractor

llm = ChatOpenAI()
response = fundingextractor(user_input, llm=llm)
```

- Anthropic

```python
from langchain_anthropic import ChatAnthropic
from fundingextractor import fundingextractor

llm = ChatAnthropic()
response = fundingextractor(user_input, llm=llm)
```

- Google PaLM or Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from fundingextractor import fundingextractor

llm = ChatGoogleGenerativeAI()
response = fundingextractor(user_input, llm=llm)
```

## Notes

- The default rate limits for LLM7's free tier are sufficient for general use.
- For higher rate limits, you can pass your API key via the `LLM7_API_KEY` environment variable or directly in the function call:

```python
response = fundingextractor(user_input, api_key="your_api_key")
```

- Obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)

## References

- The package utilizes `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/)

## Support and Issues

For issues or contributions, please visit the GitHub repository: [https://github.com/chigwell/fundingextractor](https://github.com/chigwell/fundingextractor)

## Author

- Eugene Evstafev  
- Email: hi@eugene.plus  
- GitHub: [chigwell](https://github.com/chigwell)