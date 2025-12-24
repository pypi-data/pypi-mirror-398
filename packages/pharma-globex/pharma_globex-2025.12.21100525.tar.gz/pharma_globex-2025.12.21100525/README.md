# Pharma-Globex Package
[![PyPI version](https://badge.fury.io/py/pharma-globex.svg)](https://badge.fury.io/py/pharma-globex)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/pharma-globex)](https://pepy.tech/project/pharma-globex)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Pharma-Globex is a Python library designed to analyze input texts related to global pharmaceutical trends, such as India's role in manufacturing generics. It leverages structured pattern matching to extract key points from user-provided content and generate concise, information-rich summaries suitable for reporting or decision-making. The system ensures reliable extraction even with varied phrasing by using pattern verification and retries, making it ideal for summarizing market developments, policy impacts, or industry progress.

## Installation

Install the package via pip:

```bash
pip install pharma_globex
```

## Usage

Import and use the package in your Python code:

```python
from pharma_globex import pharma_globex

response = pharma_globex(user_input="Your input text here")
```

### Parameters

- **user_input** (`str`): The input text to process.
- **llm** (`Optional[BaseChatModel]`): An instance of a language model from langchain. Defaults to using ChatLLM7.
- **api_key** (`Optional[str]`): API key for the LLM7 service. If not provided, it attempts to read from the environment variable `LLM7_API_KEY`.

### Custom LLM Support

The package defaults to using `ChatLLM7` from `langchain_llm7` (https://pypi.org/project/langchain-llm7/). Users can pass their own language model instances for flexibility:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
response = pharma_globex(user_input="Query", llm=llm)
```

Similarly, support for other LLM providers such as Anthropic, Google Generative AI, etc., is available with appropriate imports and model instantiations.

## Notes

- To get a free API key for LLM7, register at https://token.llm7.io/
- The default rate limits are sufficient for most use cases.
- For higher limits, pass your API key via environment variable `LLM7_API_KEY` or directly during function call.

## Issues

Please report issues or suggest improvements on the GitHub repository: https://github.com/...

## Author

- Eugene Evstafev (hi@eugene.plus)

## License

This project is open source and available under the MIT License.