# `transitmaplint`
[![PyPI version](https://badge.fury.io/py/transitmaplint.svg)](https://badge.fury.io/py/transitmaplint)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/transitmaplint)](https://pepy.tech/project/transitmaplint)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`transitmaplint` is a lightweight toolkit that takes a plain‑text description of a transportation or infrastructure map—such as a train network or bus route diagram—and returns a structured, concise critique.  
The output is designed to be easy to consume programmatically or to present back to designers as quick, automated feedback.

> **Author:** Eugene Evstafev  
> **Email:** hi@euegne.plus  
> **GitHub:** [chigwell](https://github.com/chigwell)  

---

## Features

* **Route clarity assessment** – Detects ambiguous terminologies and missing links in the textual map.
* **Station / stop naming** – Flags inconsistent naming, duplicate names, or overly long labels.
* **Layout suggestions** – Provides high‑level recommendations on how to reorder or group routes.
* **Consistent response format** – The function always returns a Python list of strings, each string being one feedback item.

The package leverages the open‑source LangChain framework to query an LLM. Out‑of‑the‑box it uses **ChatLLM7** from the `langchain_llm7` package, but you can freely supply any LangChain chat model (OpenAI, Anthropic, Google, etc.).

---

## Installation

```bash
pip install transitmaplint
```

`transitmaplint` pulls in its dependencies automatically:
* `langchain-core`
* `langchain-llm7` (default LLM provider)
* `llmatch_messages`

---

## Quick Start

```python
from transitmaplint import transitmaplint

# Sample map description
user_input = """
Route A: Station 1 -> Station 2 -> Station 3
Route B: Station 3 -> Station 4 -> Station 5
"""

feedback = transitmaplint(user_input)

for i, item in enumerate(feedback, 1):
    print(f"{i}. {item}")
```

The output will be a list of feedback strings such as:
```
1. Route B shares Station 3 with Route A – consider adding a buffer station.
2. Station names are concise, but "Station 1" and "Station 2" could be more descriptive.
3. The overall layout flows linearly; adding a cross‑link between Route A and Route B at Station 3 would improve connectivity.
```

---

## Advanced Usage – Providing Your Own LLM

The `transitmaplint` function accepts an optional `llm` argument that can be any instance of `langchain_core.language_models.BaseChatModel`.  
Below are examples of using popular providers.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from transitmaplint import transitmaplint

llm = ChatOpenAI()  # configure as needed (API key, model, etc.)
feedback = transitmaplint(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from transitmaplint import transitmaplint

llm = ChatAnthropic()
feedback = transitmaplint(user_input, llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from transitmaplint import transitmaplint

llm = ChatGoogleGenerativeAI()
feedback = transitmaplint(user_input, llm=llm)
```

---

## Configuration – LLM7 API Key

If you want to use the default **ChatLLM7** but with a higher rate limit or a personal key:

```bash
export LLM7_API_KEY="your-ultra-key-here"
```

or pass it directly:

```python
feedback = transitmaplint(user_input, api_key="your-ultra-key-here")
```

The free tier of LLM7 is usually sufficient for most small‑to‑medium map checks.

> **Getting an LLM7 key** – Register for free at [LLM7](https://token.llm7.io/).

---

## Supported Return Type

```python
List[str]
```

Each item in the list is a well‑structured sentence.  The function guarantees that the returned data matches the regex pattern defined internally (`pattern` from `transitmaplint.prompts`).  This makes it straightforward to iteratively parse or store feedback.

---

## Development & Issues

<li>Issues, feature requests, and discussion: <https://github.com/chigwell/transitmaplint/issues></li>

---

## License

MIT License – feel free to use, modify, and distribute.

--- 

**Want to contribute?** Fork the repository, create a new feature branch, and open a pull request.  We're happy to receive documentation, new prompt templates, or improvements to the regex checking logic.