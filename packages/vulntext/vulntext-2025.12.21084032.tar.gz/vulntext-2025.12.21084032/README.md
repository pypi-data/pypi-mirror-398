# vulntext - Vulnerability Text Analyzer
[![PyPI version](https://badge.fury.io/py/vulntext.svg)](https://badge.fury.io/py/vulntext)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vulntext)](https://pepy.tech/project/vulntext)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`vulntext` is a lightweight Python package that extracts structured vulnerability information from natural‑language descriptions of software security issues. By feeding the package a text (e.g., a bug report, CVE description, or a security advisory) it returns an array of structured data items such as vulnerability type, severity level, affected component, and recommended remediation steps.

## Features

- Simple, self‑contained interface
- Uses *LLM7* by default (free tier, suitable for most uses)
- Fully flexible: plug in any LangChain compatible LLM
- Generates results that match a user‑defined regex pattern

## Installation

```bash
pip install vulntext
```

## Quick Start

```python
from vulntext import vulntext

user_input = """
A buffer overflow bug in the network packet parser allows an attacker to crash
the service and potentially execute arbitrary code. The vulnerability is
present in version 2.3.4 of the packet-processor library.
"""

# Basic usage (uses the default LLM7 wrapper)
results = vulntext(user_input)
print(results)
```

You will see an output that looks roughly like:

```json
[
  {
    "type": "Buffer Overflow",
    "severity": "High",
    "component": "packet-processor",
    "version": "2.3.4",
    "remediation": "Update to 2.3.5 or patch the parser."
  }
]
```

## Using a Custom LLM

`vulntext` accepts a *LangChain* `BaseChatModel` instance. This allows you to use any provider supported by LangChain:

```python
# OpenAI
from langchain_openai import ChatOpenAI
from vulntext import vulntext

llm = ChatOpenAI()
response = vulntext(user_input, llm=llm)

# Anthropic
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = vulntext(user_input, llm=llm)

# Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = vulntext(user_input, llm=llm)
```

When a custom LLM is provided, the `api_key` argument is ignored because the key is managed by the wrapper you pass in.

## Optional API Key for LLM7

If you want to override the free LLM7 tier or need higher rate limits, supply your own key either as an environment variable or directly:

```bash
export LLM7_API_KEY=your_basic_api_key_here
```

or

```python
response = vulntext(user_input, api_key="your_basic_api_key_here")
```

You can obtain a free key by registering at [LLM7](https://token.llm7.io/).

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text containing the vulnerability description. |
| `llm` | `Optional[BaseChatModel]` | A LangChain chat model instance. When omitted, the package falls back to the bundled `ChatLLM7`. |
| `api_key` | `Optional[str]` | Your LLM7 API key. Ignored if `llm` is supplied. Note that the free tier is usually sufficient for most uses. |

## Development & Bug Reports

- Repository: <https://github.com/chigwell/vulntext>
- Issues: <https://github.com/chigwell/vulntext/issues>

## License

MIT

## Author

Eugene Evstafev  
📧 hi@euegne.plus  
🐙 @chigwell

--- 

Happy hacking! 🎯