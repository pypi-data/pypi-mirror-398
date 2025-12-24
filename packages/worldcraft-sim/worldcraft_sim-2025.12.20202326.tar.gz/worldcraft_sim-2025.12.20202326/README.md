# Worldcraft-Sim

[![PyPI version](https://badge.fury.io/py/worldcraft-sim.svg)](https://badge.fury.io/py/worldcraft-sim)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/worldcraft-sim)](https://pepy.tech/project/worldcraft-sim)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue.svg)](https://www.linkedin.com/in/chigwell)

## Overview

Worldcraft-Sim is a Python package that allows users to type plain text descriptions of imaginary worlds, defining rules, ecosystems, and events. Using LLM7 and `llmatch-messages`, the package returns a structured, step-by-step simulation narrative that responds to those inputs. The system interprets the user's creative prompts, verifies them with regex patterns, and generates a formatted output that can be parsed back into a programmatic representation of the evolving world, enabling playful exploration of alternate realities without processing raw documents or media.

## Installation

You can install the package using pip:

```bash
pip install worldcraft_sim
```

## Usage

Here is an example of how to use the `worldcraft_sim` function:

```python
from worldcraft_sim import worldcraft_sim

# Example usage with default LLM7
response = worldcraft_sim(user_input="Describe a fantasy world with magical creatures and ancient ruins.")
print(response)
```

### Input Parameters

- `user_input`: `str` : The user input text to process.
- `llm`: `Optional[BaseChatModel]` : The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key`: `Optional[str]` : The API key for LLM7. If not provided, it will be fetched from the environment variable `LLM7_API_KEY`.

### Using a Custom LLM

You can use a custom LLM by passing an instance of `BaseChatModel`. For example, to use OpenAI, Anthropic, or Google's Generative AI:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from worldcraft_sim import worldcraft_sim

llm = ChatOpenAI()
response = worldcraft_sim(user_input="Describe a fantasy world with magical creatures and ancient ruins.", llm=llm)
print(response)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from worldcraft_sim import worldcraft_sim

llm = ChatAnthropic()
response = worldcraft_sim(user_input="Describe a fantasy world with magical creatures and ancient ruins.", llm=llm)
print(response)
```

#### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from worldcraft_sim import worldcraft_sim

llm = ChatGoogleGenerativeAI()
response = worldcraft_sim(user_input="Describe a fantasy world with magical creatures and ancient ruins.", llm=llm)
print(response)
```

### API Key

The default rate limits for LLM7's free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call:

```python
response = worldcraft_sim(user_input="Describe a fantasy world with magical creatures and ancient ruins.", api_key="your_api_key")
```

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/worldcraft-sim).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)