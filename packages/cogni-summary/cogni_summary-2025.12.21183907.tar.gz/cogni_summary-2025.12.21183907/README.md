# Cogni-Summary
[![PyPI version](https://badge.fury.io/py/cogni-summary.svg)](https://badge.fury.io/py/cogni-summary)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/cogni-summary)](https://pepy.tech/project/cogni-summary)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Extract key insights, definitions, and actionable takeaways from any text input using a large language model.

## Installation
```bash
pip install cogni_summary
```

## Usage
```python
from cogni_summary import cogni_summary

response = cogni_summary(user_input="Your text here")
```

You can pass additional parameters to customize the model:

- `user_input`: The text to be summarized (required).
- `llm`: The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key`: The API key for LLM7. If not provided, the default rate limits for LLM7 free tier will be used.

You can safely pass your own LLM instance (e.g., OpenAI, Anthropic, Google) using the corresponding LangChain library. For example, to use the OpenAI LLM:
```python
from langchain_openai import ChatOpenAI
from cogni_summary import cogni_summary

llm = ChatOpenAI()
response = cogni_summary(user_input, llm=llm)
```

Alternatively, to use the Anthropic LLM:
```python
from langchain_anthropic import ChatAnthropic
from cogni_summary import cogni_summary

llm = ChatAnthropic()
response = cogni_summary(user_input, llm=llm)
```

Or to use the Google LLM:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from cogni_summary import cogni_summary

llm = ChatGoogleGenerativeAI()
response = cogni_summary(user_input, llm=llm)
```

If you need higher rate limits for LLM7, you can pass your own API key as an environment variable `LLM7_API_KEY` or directly as the `api_key` parameter.

Get a free API key by registering at <https://token.llm7.io/>.

## Documentation

For more information about the LangChain libraries used in this package, please refer to:

- [LangChain LLM7 documentation](https://docs.langchain.com/docs/tutorials/llm7/)
- [LangChain OpenAI documentation](https://docs.langchain.com/docs/tutorials/openai/)
- [LangChain Anthropic documentation](https://docs.langchain.com/docs/tutorials/anthropic/)
- [LangChain Google GenAI documentation](https://docs.langchain.com/docs/tutorials/google-genai/)

## Contributing

Please submit any issues or pull requests to our GitHub repository: <https://github.com/chigwell/cogni-summary>

## Author

Eugene Evstafev (<hi@eugene.plus>)