# passgen-llm
[![PyPI version](https://badge.fury.io/py/passgen-llm.svg)](https://badge.fury.io/py/passgen-llm)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/passgen-llm)](https://pepy.tech/project/passgen-llm)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`passgen_llm` is a Python package that leverages a Language Model (LLM) to generate structured, formatted pass content for Apple Wallet. It takes user-provided text input, such as event details, membership information, or coupon data, and ensures the output adheres to Apple's pass requirements by validating the response with pattern matching. This makes it easy for users to create custom, scannable passes without manual formatting.

## Features

- **Automated Pass Generation**: Automatically generate Apple Wallet passes from user-provided text input.
- **Pattern Matching**: Ensures the generated pass content adheres to Apple's pass requirements.
- **Flexible LLM Integration**: Supports custom LLM instances, including OpenAI, Anthropic, and Google Generative AI.
- **Easy Installation**: Simple installation process with `pip`.

## Installation

You can install `passgen_llm` using `pip`:

```bash
pip install passgen_llm
```

## Usage

Here's a basic example of how to use `passgen-llm`:

```python
from passgen_llm import passgen_llm

user_input = "Event: Tech Conference, Date: 2023-10-15, Location: San Francisco"
response = passgen_llm(user_input)
print(response)
```

### Input Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

### Custom LLM Instances

You can use custom LLM instances by passing them to the `passgen_llm` function. Here are examples using different LLMs:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from passgen_llm import passgen_llm

llm = ChatOpenAI()
response = passgen_llm(user_input, llm=llm)
print(response)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from passgen_llm import passgen_llm

llm = ChatAnthropic()
response = passgen_llm(user_input, llm=llm)
print(response)
```

#### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from passgen_llm import passgen_llm

llm = ChatGoogleGenerativeAI()
response = passgen_llm(user_input, llm=llm)
print(response)
```

### API Key

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call:

```python
response = passgen_llm(user_input, api_key="your_api_key")
```

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/passgen-llm).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)