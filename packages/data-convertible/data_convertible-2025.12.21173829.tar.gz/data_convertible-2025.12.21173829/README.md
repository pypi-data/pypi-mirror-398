# data-convertible
[![PyPI version](https://badge.fury.io/py/data-convertible.svg)](https://badge.fury.io/py/data-convertible)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/data-convertible)](https://pepy.tech/project/data-convertible)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that provides a structured and reliable way to process user input related to common developer utilities such as JSON, Base64, URL, and hash operations. It uses an LLM to interpret user requests and return formatted, validated outputs, ensuring consistency and correctness in the results.

## Installation

You can install the package via pip:

```bash
pip install data_convertible
```

## Usage

Here's a basic example of how to use the package:

```python
from data_convertible import data_convertible

# Process user input
response = data_convertible("Convert 'hello' to base64")
print(response)
```

### Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used, or a default free tier key will be used.

### Using a Custom LLM

You can pass your own LangChain LLM instance if you want to use another LLM provider. For example, to use OpenAI:

```python
from langchain_openai import ChatOpenAI
from data_convertible import data_convertible

llm = ChatOpenAI()
response = data_convertible("Validate this JSON: {'name': 'John'}", llm=llm)
```

To use Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from data_convertible import data_convertible

llm = ChatAnthropic()
response = data_convertible("Encode this URL: example.com?q=test", llm=llm)
```

To use Google Generative AI:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from data_convertible import data_convertible

llm = ChatGoogleGenerativeAI()
response = data_convertible("Compute SHA256 of 'hello'", llm=llm)
```

### API Key for LLM7

By default, the package uses ChatLLM7 from [langchain_llm7](https://pypi.org/project/langchain-llm7/) with a free tier API key. The default rate limits are sufficient for most use cases. If you need higher rate limits, you can:

- Set the environment variable `LLM7_API_KEY` to your API key.
- Pass the API key directly: `data_convertible(..., api_key="your_api_key")`.

You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Contributing

If you encounter any issues or have suggestions for improvements, please open an issue on [GitHub](https://github.com/chigwell/data-convertible/issues).

## Author

- **Eugene Evstafev** - [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)