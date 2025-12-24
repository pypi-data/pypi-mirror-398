# Privacy Idea Struct

[![PyPI version](https://badge.fury.io/py/privacy-idea-struct.svg)](https://pypi.org/project/privacy-idea-struct/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/personalized-badge/privacy-idea-struct?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads)](https://pepy.tech/project/privacy-idea-struct)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/eugene-evstafev/)

A Python package that enables users to provide simple text inputs about innovative, privacy-focused services and receive structured summaries or descriptions of their ideas.

## Installation

```bash
pip install privacy_idea_struct
```

## Usage

```python
from privacy_idea_struct import privacy_idea_struct

response = privacy_idea_struct(
    user_input="A phone company that doesn't collect personal data.",
    api_key="your_api_key_here"
)
print(response)
```

## Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Using Different LLMs

You can safely pass your own LLM instance if you want to use another LLM. Here are examples for different LLMs:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from privacy_idea_struct import privacy_idea_struct

llm = ChatOpenAI()
response = privacy_idea_struct(
    user_input="A phone company that doesn't collect personal data.",
    llm=llm
)
print(response)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from privacy_idea_struct import privacy_idea_struct

llm = ChatAnthropic()
response = privacy_idea_struct(
    user_input="A phone company that doesn't collect personal data.",
    llm=llm
)
print(response)
```

### Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from privacy_idea_struct import privacy_idea_struct

llm = ChatGoogleGenerativeAI()
response = privacy_idea_struct(
    user_input="A phone company that doesn't collect personal data.",
    llm=llm
)
print(response)
```

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly via the `api_key` parameter. You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/privacy-idea-struct/issues).

## Author

- **Eugene Evstafev**
- **Email**: hi@eugene.plus
- **GitHub**: [chigwell](https://github.com/chigwell)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.