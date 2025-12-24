# CloudInsight Extractor
[![PyPI version](https://badge.fury.io/py/cloudinsight-extractor.svg)](https://badge.fury.io/py/cloudinsight-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cloudinsight-extractor)](https://pepy.tech/project/cloudinsight-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


CloudInsight Extractor is a Python package designed to analyze and extract structured insights from user-submitted summaries or descriptions related to cloud infrastructure topics. Given an input text about a specific subject like cloud infrastructure developments, the package uses a language model to identify key themes, trends, and innovative points, presenting the results in a clear, organized format. This helps users quickly grasp essential information without manually sifting through lengthy descriptions, facilitating better understanding and decision-making in technical domains.

## Installation

To install the CloudInsight Extractor package, run the following command:

```bash
pip install cloudinsight_extractor
```

## Usage

Here is an example of how to use the `cloudinsight_extractor` function:

```python
from cloudinsight_extractor import cloudinsight_extractor

# Example usage with default LLM7
response = cloudinsight_extractor(user_input="Your input text here")
print(response)
```

### Using a Custom LLM

You can also use a custom LLM instance from LangChain. Here are examples for different LLM providers:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from cloudinsight_extractor import cloudinsight_extractor

llm = ChatOpenAI()
response = cloudinsight_extractor(user_input="Your input text here", llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from cloudinsight_extractor import cloudinsight_extractor

llm = ChatAnthropic()
response = cloudinsight_extractor(user_input="Your input text here", llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from cloudinsight_extractor import cloudinsight_extractor

llm = ChatGoogleGenerativeAI()
response = cloudinsight_extractor(user_input="Your input text here", llm=llm)
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the package will use the environment variable `LLM7_API_KEY` or a default value.

## Default LLM

By default, the package uses `ChatLLM7` from the `langchain_llm7` package. You can find more information about `ChatLLM7` [here](https://pypi.org/project/langchain-llm7/).

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues or have suggestions, please open an issue on the [GitHub repository](https://github.com/chigwell/cloudinsight-extractor).

## Author

- **Eugene Evstafev**
  - Email: hi@eugene.plus
  - GitHub: [chigwell](https://github.com/chigwell)