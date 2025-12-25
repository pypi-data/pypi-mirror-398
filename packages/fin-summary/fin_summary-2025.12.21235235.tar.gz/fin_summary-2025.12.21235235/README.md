# fin-summary
[![PyPI version](https://badge.fury.io/py/fin-summary.svg)](https://badge.fury.io/py/fin-summary)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/fin-summary)](https://pepy.tech/project/fin-summary)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**fin-summary** is a lightweight Python package that extracts structured, actionable information from user‑provided text describing financial transaction issues (e.g., processing fees, settlement delays). It uses pattern matching combined with a language model to identify key details such as issue type, amount, timeline, and recommended steps, returning a concise summary that can be directly acted upon.

## Features

- Simple one‑function API (`fin_summary`)  
- Works out‑of‑the‑box with the default **ChatLLM7** model from `langchain_llm7`  
- Plug‑in friendly – you can provide any LangChain‑compatible LLM (OpenAI, Anthropic, Google, etc.)  
- Returns a list of extracted strings that match the supplied regex pattern  

## Installation

```bash
pip install fin_summary
```

## Quick Start

```python
from fin_summary import fin_summary

# Example user description of a problem
user_input = """
I was charged an extra $15 processing fee on my $200
transfer that should have settled yesterday, but it still shows
as pending. What should I do?
"""

# Use the default ChatLLM7 model (requires an API key)
summary = fin_summary(user_input)

print(summary)
# -> ['Issue type: processing fee', 'Amount: $15', 'Original amount: $200', ...]
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The free‑form text describing the financial issue. |
| `llm` | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the package creates a `ChatLLM7` instance using the provided `api_key` or the `LLM7_API_KEY` environment variable. |
| `api_key` | `Optional[str]` | API key for LLM7. If not supplied, the package reads `LLM7_API_KEY` from the environment. |

## Using a Custom LLM

You can pass any LangChain LLM that implements `BaseChatModel`. Below are examples with popular providers.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from fin_summary import fin_summary

llm = ChatOpenAI()
response = fin_summary(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from fin_summary import fin_summary

llm = ChatAnthropic()
response = fin_summary(user_input, llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from fin_summary import fin_summary

llm = ChatGoogleGenerativeAI()
response = fin_summary(user_input, llm=llm)
```

## API Key & Rate Limits

- **Default LLM**: `ChatLLM7` (from `langchain_llm7`)  
  Documentation: https://pypi.org/project/langchain-llm7/  
- Free‑tier rate limits are sufficient for typical usage of this package.  
- To increase limits, provide your own API key:  

```bash
export LLM7_API_KEY="your_api_key"
```

or directly in code:

```python
response = fin_summary(user_input, api_key="your_api_key")
```

You can obtain a free API key by registering at https://token.llm7.io/.

## Contributing & Issues

If you encounter any problems or have feature requests, please open an issue on GitHub:

[https://github.com/chigwell/fin-summary/issues](https://github.com/chigwell/fin-summary/issues)

## Author

**Eugene Evstafev**  
Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

Happy summarizing! 🚀