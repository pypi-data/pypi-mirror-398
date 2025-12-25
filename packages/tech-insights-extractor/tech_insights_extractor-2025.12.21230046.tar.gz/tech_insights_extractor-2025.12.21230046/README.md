# tech-insights-extractor
[![PyPI version](https://badge.fury.io/py/tech-insights-extractor.svg)](https://badge.fury.io/py/tech-insights-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/tech-insights-extractor)](https://pepy.tech/project/tech-insights-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`tech_insights_extractor` is a lightweight Python package that lets you quickly turn unstructured text about recent technological advancements into structured, concise insights.  
It uses a language‑model‑based prompt‐engineering approach combined with regular‑expression validation to:

* Summarise key innovations
* Identify the nature of breakthroughs
* Output the information in a consistent, easy‑to‑consume format

The package comes with a default LLM implementation (`ChatLLM7` from `langchain_llm7`), but you can inject any LangChain `BaseChatModel` (OpenAI, Anthropic, Google Gemini, etc.) for customized behaviour.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Parameters](#parameters)
  - [Default LLM](#default-llm)
  - [Custom LLMs](#custom-llms)
- [Rate Limits & API Key](#rate-limits--api-key)
- [Troubleshooting & Issues](#troubleshooting--issues)
- [License & Contact](#license--contact)

---

## Installation

```bash
pip install tech_insights_extractor
```

---

## Quick Start

```python
from tech_insights_extractor import tech_insights_extractor

text = """
Recent research has unveiled a novel quantum‑error correction code that reduces surface‑code overhead by 30%. ...
"""

# Using the default ChatLLM7
insights = tech_insights_extractor(user_input=text)

print(insights)
# ['Summary: ...', 'Key Innovation: ...', 'Category: Quantum Computing']
```

---

## Usage

```python
from tech_insights_extractor import tech_insights_extractor
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The raw text you want to analyse. |
| `llm` | `Optional[BaseChatModel]` | A LangChain chat model to send prompts to. If omitted, the package falls back to its built‑in `ChatLLM7`. |
| `api_key` | `Optional[str]` | The API key for LLM7. If omitted, the package checks the `LLM7_API_KEY` environment variable, and finally defaults to `"None"` (free tier). |

### Default LLM

If you do **not** supply an `llm`, `tech_insights_extractor` will automatically instantiate a `ChatLLM7` with the provided or environment key.

```python
# No LLM arg – uses ChatLLM7 internally
insights = tech_insights_extractor(user_input=text)
```

### Custom LLMs

You can drop in any LangChain `BaseChatModel`. Examples below:

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from tech_insights_extractor import tech_insights_extractor

llm = ChatOpenAI(model="gpt-4o-mini")
insights = tech_insights_extractor(user_input=text, llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from tech_insights_extractor import tech_insights_extractor

llm = ChatAnthropic()
insights = tech_insights_extractor(user_input=text, llm=llm)
```

#### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from tech_insights_extractor import tech_insights_extractor

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
insights = tech_insights_extractor(user_input=text, llm=llm)
```

---

## Rate Limits & API Key

The free tier of LLM7 offers generous limits for most projects.  
If you require higher throughput or want to avoid the default key:

1. Register for an API key at <https://token.llm7.io/>.  
2. Pass it directly:

```python
insights = tech_insights_extractor(user_input=text, api_key="your_api_key_here")
```

or export it as an environment variable:

```bash
export LLM7_API_KEY="your_api_key_here"
```

---

## Troubleshooting & Issues

Please report bugs or feature requests at:
<https://github.com/chigwell/tech-insights-extractor/issues>

---

## License & Contact

- **Author:** Eugene Evstafev  
- **Email:** hi@euegne.plus  
- **GitHub:** @chigwell

The project is open source under the MIT License. Feel free to fork, modify, and contribute!

---

*Happy extracting!*