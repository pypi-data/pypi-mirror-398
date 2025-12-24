# promptify-summary
[![PyPI version](https://badge.fury.io/py/promptify-summary.svg)](https://badge.fury.io/py/promptify-summary)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/promptify-summary)](https://pepy.tech/project/promptify-summary)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`promptify_summary` is a lightweight Python package that turns arbitrary text
(e.g. video titles, headlines, or any user‑supplied string) into concise,
structured summaries using a large language model.  
The package relies on pattern matching to guarantee consistent, predictable
output regardless of the LLM provider. It works with the default
`ChatLLM7` backend out of the box while also allowing you to plug in any
`langchain` compatible LLM.

## Quick Start

```bash
pip install promptify_summary
```

```python
# Basic usage with the default LLM7 backend
from promptify_summary import promptify_summary

user_input = "Learn how to deploy a Docker container in 5 minutes!"
summary = promptify_summary(user_input)

print(summary)
# >>> ['Deploy Docker Container', '5 minutes', ...]  # Example output
```

## Custom LLM Support

You can swap the default `ChatLLM7` for any LangChain LLM.  
Below are examples with OpenAI, Anthropic, and Google Generative AI.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from promptify_summary import promptify_summary

llm = ChatOpenAI()          # Uses default OpenAI key in environment
user_input = "How to tune a PostgreSQL database?"
summary = promptify_summary(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from promptify_summary import promptify_summary

llm = ChatAnthropic()       # Uses your Anthropic key in environment
summary = promptify_summary("Explain quantum entanglement.", llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from promptify_summary import promptify_summary

llm = ChatGoogleGenerativeAI()   # Uses your Google key in environment
summary = promptify_summary("What is Python 3.11?", llm=llm)
```

## Function Signature

```python
promptify_summary(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Text to summarize. |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM instance. If `None`, `ChatLLM7` is used. |
| `api_key` | `Optional[str]` | LLM7 API key. If omitted, the package looks for the `LLM7_API_KEY` environment variable, falling back to a placeholder key. |

The function returns a list of strings extracted from the LLM’s response that
match the internal regular‑expression pattern, ensuring output consistency.

## Default LLM7 Configuration

The default `ChatLLM7` backend is accessed via the
[`langchain_llm7`](https://pypi.org/project/langchain-llm7/) package.
If you want to change the API key (for higher rate limits or a different
account) provide the key directly or set the environment variable:

```bash
export LLM7_API_KEY="your_free_or_paid_api_key"
```

Or pass it programmatically:

```python
summary = promptify_summary("Sample text", api_key="your_api_key")
```

You can obtain a free key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Rate Limits

The LLM7 free tier rate limits are sufficient for most casual or small‑scale
projects. For more intensive workloads, consider upgrading your LLM7 account
to increase limits or supply your own LLM.

## Author & Support

- **Author:** Eugene Evstafev
- **Email:** hi@euegne.plus
- **GitHub:** [chigwell](https://github.com/chigwell)

For issues, feature requests, or questions, open an issue on our
[GitHub repository](https://github.com/chigwell/promptify_summary).

Enjoy automating structured content generation with `promptify-summary`!