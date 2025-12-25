# FoodTrend Analyzer
[![PyPI version](https://badge.fury.io/py/foodtrend-analyzer.svg)](https://badge.fury.io/py/foodtrend-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/foodtrend-analyzer)](https://pepy.tech/project/foodtrend-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


FoodTrend Analyzer is a Python package designed to analyze and summarize food trends by processing text inputs. Users can input articles, social media posts, or any text discussing food preferences and consumption patterns. The package uses `llmatch-messages` to ensure structured responses, providing insights into trends like the shift from pizza to fried chicken among Gen Z. It extracts key points, identifies trends, and presents them in a consistent format, making it easier to understand and act on food industry insights.

## Features

- **Text Processing**: Analyze articles, social media posts, and other text inputs to extract food trends.
- **Structured Responses**: Use `llmatch-messages` to ensure consistent and structured output.
- **Customizable LLM**: Use the default `ChatLLM7` from `langchain_llm7` or pass your own LLM instance for flexibility.
- **API Key Management**: Easily manage API keys for `ChatLLM7` via environment variables or direct input.

## Installation

You can install the package using pip:

```bash
pip install foodtrend_analyzer
```

## Usage

Here is a basic example of how to use the `foodtrend_analyzer` package:

```python
from foodtrend_analyzer import foodtrend_analyzer

# Example user input
user_input = "Gen Z is shifting from pizza to fried chicken."

# Analyze the input
response = foodtrend_analyzer(user_input)

# Print the response
print(response)
```

### Input Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for `ChatLLM7`. If not provided, the key will be fetched from the environment variable `LLM7_API_KEY`.

### Custom LLM Usage

You can use different LLMs by passing your own LLM instance. Here are examples using OpenAI, Anthropic, and Google:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from foodtrend_analyzer import foodtrend_analyzer

llm = ChatOpenAI()
response = foodtrend_analyzer(user_input, llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from foodtrend_analyzer import foodtrend_analyzer

llm = ChatAnthropic()
response = foodtrend_analyzer(user_input, llm=llm)
```

#### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from foodtrend_analyzer import foodtrend_analyzer

llm = ChatGoogleGenerativeAI()
response = foodtrend_analyzer(user_input, llm=llm)
```

### API Key Management

The default rate limits for `LLM7` free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call:

```python
response = foodtrend_analyzer(user_input, api_key="your_api_key")
```

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/foodtrend-analyzer).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)