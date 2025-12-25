# forum-guard
[![PyPI version](https://badge.fury.io/py/forum-guard.svg)](https://badge.fury.io/py/forum-guard)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/forum-guard)](https://pepy.tech/project/forum-guard)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to facilitate structured and reliable textual interactions within a global forum environment. It processes user inputs—such as comments, questions, and feedback—using pattern matching and retries to extract key information, topics, or sentiments, ensuring consistent and meaningful responses. The system enables moderators or automated tools to identify and categorize submissions effectively, fostering authentic and unfiltered conversations while maintaining high-quality, structured exchanges based solely on the provided text data.

## Installation

```bash
pip install forum_guard
```

## Usage

Here's an example of how to use the `forum_guard` function in Python:

```python
from forum_guard import forum_guard

user_input = "Your user input text here."
response = forum_guard(user_input)
print(response)
```

### Input Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): An instance of a langchain.llm core language model to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for `ChatLLM7`. If not provided, it attempts to read from the environment variable `LLM7_API_KEY`.

### Custom LLM Usage

You can pass your own language model instance to `forum_guard`. Supported models include, but are not limited to:

- [Langchain OpenAI](https://pypi.org/project/langchain-openai/)
  
```python
from langchain_openai import ChatOpenAI
from forum_guard import forum_guard

llm = ChatOpenAI()
response = forum_guard(user_input, llm=llm)
```

- [Langchain Anthropic](https://pypi.org/project/langchain-anthropic/)

```python
from langchain_anthropic import ChatAnthropic
from forum_guard import forum_guard

llm = ChatAnthropic()
response = forum_guard(user_input, llm=llm)
```

- [Langchain Google Generative AI](https://pypi.org/project/langchain-google-generative-ai/)

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from forum_guard import forum_guard

llm = ChatGoogleGenerativeAI()
response = forum_guard(user_input, llm=llm)
```

### Notes

- The default `ChatLLM7` is based on the `langchain_llm7` package. You can install it via:

```bash
pip install langchain-llm7
```

- To increase rate limits, you can set your own `LLM7_API_KEY` in environment variables or pass it directly:

```python
response = forum_guard(user_input, api_key="your_api_key")
```

- You can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/)

## Support

For issues and feature requests, visit the GitHub repository:
[https://github.com/yourusername/forum-guard/issues](https://github.com/yourusername/forum-guard/issues)

## Author

Eugene Evstafev (chigwell)  
Email: hi@euegne.plus