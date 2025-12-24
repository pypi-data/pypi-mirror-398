# GreekLexiconRejuvenator
[![PyPI version](https://badge.fury.io/py/greeklexiconrejuvenator.svg)](https://badge.fury.io/py/greeklexiconrejuvenator)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/greeklexiconrejuvenator)](https://pepy.tech/project/greeklexiconrejuvenator)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


GreekLexiconRejuvenator is a Python package designed to analyze user-provided text about ancient Greek terms and generate a structured summary highlighting terms that should be revitalized in modern language. It leverages pattern matching to identify key terms, their definitions, and relevance, ensuring clear and consistent output.

## Features

- **Text Analysis**: Processes input text to identify ancient Greek terms.
- **Pattern Matching**: Uses regex patterns to extract and format relevant terms.
- **Flexible LLM Integration**: Supports custom language models from LangChain or defaults to ChatLLM7.
- **Robust Error Handling**: Includes retry mechanisms and diagnostic messages for robustness.

## Installation

You can install the package using pip:

```bash
pip install greeklexiconrejuvenator
```

## Usage

Here's a basic example of how to use the `greeklexiconrejuvenator` package:

```python
from greeklexiconrejuvenator import greeklexiconrejuvenator

# Example usage with default LLM
response = greeklexiconrejuvenator(user_input="Your text about ancient Greek terms here.")
print(response)
```

### Custom LLM Integration

You can also use your own language model from LangChain. Here are examples with different LLMs:

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from greeklexiconrejuvenator import greeklexiconrejuvenator

llm = ChatOpenAI()
response = greeklexiconrejuvenator(user_input="Your text about ancient Greek terms here.", llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from greeklexiconrejuvenator import greeklexiconrejuvenator

llm = ChatAnthropic()
response = greeklexiconrejuvenator(user_input="Your text about ancient Greek terms here.", llm=llm)
print(response)
```

#### Using Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from greeklexiconrejuvenator import greeklexiconrejuvenator

llm = ChatGoogleGenerativeAI()
response = greeklexiconrejuvenator(user_input="Your text about ancient Greek terms here.", llm=llm)
print(response)
```

### API Key

The default rate limits for LLM7 free tier are sufficient for most use cases. If you need higher rate limits, you can pass your own API key via the `api_key` parameter or set the environment variable `LLM7_API_KEY`.

```python
response = greeklexiconrejuvenator(user_input="Your text about ancient Greek terms here.", api_key="your_api_key")
```

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/greeklexiconrejuvenator).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)