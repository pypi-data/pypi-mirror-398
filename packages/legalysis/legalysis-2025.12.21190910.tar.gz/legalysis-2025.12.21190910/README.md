# legalysis
[![PyPI version](https://badge.fury.io/py/legalysis.svg)](https://badge.fury.io/py/legalysis)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/legalysis)](https://pepy.tech/project/legalysis)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`legalysis` is a lightweight Python package designed to transform unstructured legal case summaries or dispute narratives into structured insights.  
It extracts key elements such as parties, core legal issues, outcomes, and lessons learned, returning the information in a consistent, easy‑to‑parse format.

The package uses pattern matching to guarantee that the LLM output matches a predefined regex, ensuring reliable, reproducible results across different cases.

---

## Features

- **Zero‑configuration LLM usage** – defaults to the free tier of **ChatLLM7** from `langchain_llm7`.
- **Pattern‑matched output** – guarantees that extracted data follows a standard format.
- **Optional custom LLM** – seamlessly switch to OpenAI, Anthropic, Google Gemini, or any other Langchain-compatible model.
- **Simple API** – just one function call: `legalysis(user_input, llm=..., api_key=...)`.

---

## Installation

```bash
pip install legalysis
```

---

## Quickstart

```python
from legalysis import legalysis

# Simple usage with default ChatLLM7
user_input = """
In Smith v. Jones, the plaintiff alleged that the defendant breached a contract
by failing to deliver goods within the agreed timeframe. The court ruled in favor
of the plaintiff, awarding damages and injunction. Key lesson: always include
a clear delivery clause in contracts.
"""
response = legalysis(user_input)
print(response)
```

---

## Parameters

```python
legalysis(user_input: str,
          api_key: Optional[str] = None,
          llm: Optional[BaseChatModel] = None) -> List[str]
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Raw legal narrative text to analyze. |
| `llm` | `Optional[BaseChatModel]` | Langchain LLM instance. If omitted, the package will instantiate the default **ChatLLM7**. |
| `api_key` | `Optional[str]` | API key for LLM7. If omitted, the package looks for the environment variable `LLM7_API_KEY`; if still unavailable, it falls back to the free‑tier default key. |

---

## Using Your Own LLM

`legalysis` accepts any Langchain-compatible model. For example:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from legalysis import legalysis

llm = ChatOpenAI(temperature=0)
response = legalysis(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from legalysis import legalysis

llm = ChatAnthropic(temperature=0.5)
response = legalysis(user_input, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from legalysis import legalysis

llm = ChatGoogleGenerativeAI(temperature=0.2)
response = legalysis(user_input, llm=llm)
```

---

## Rate Limits & API Keys

- The **ChatLLM7** free tier is sufficient for most developers’ needs.  
- To increase limits, start a paid plan on LLM7 and supply your key via the environment variable `LLM7_API_KEY` or directly in the function call:

```python
response = legalysis(user_input, api_key="YOUR_API_KEY")
```

You can obtain a free key by registering at <https://token.llm7.io/>.

---

## Issues & Support

If you find bugs or have feature requests, please open an issue here:
<https://github.com/chigwell/legalysis/issues>

---

## Author

- **Eugene Evstafev**  
- Email: hi@euegne.plus  
- GitHub: <https://github.com/chigwell>