# Optimistic‑Pessimistic Evaluator
[![PyPI version](https://badge.fury.io/py/optimistic-pessimistic-evaluator.svg)](https://badge.fury.io/py/optimistic-pessimistic-evaluator)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/optimistic-pessimistic-evaluator)](https://pepy.tech/project/optimistic-pessimistic-evaluator)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package that lets you compare **optimistic** and **pessimistic** validation strategies for any textual description or data snippet.  
It builds structured prompts, queries a language model, matches the response against a strict regex pattern, and returns a clear, machine‑readable report indicating which approach performs better based on your criteria.

---

## Installation

```bash
pip install optimistic_pessimistic_evaluator
```

---

## Quick Start

```python
from optimistic_pessimistic_evaluator import optimistic_pessimistic_evaluator

user_input = """
A user uploads a file. The system checks the file size and type.
We want to know whether an optimistic (early‑exit) or a pessimistic (full‑check) approach is more efficient.
"""

# Use the default LLM7 instance (you need an API key in LLM7_API_KEY env var)
report = optimistic_pessimistic_evaluator(user_input)

print(report)
```

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text to be evaluated. |
| `llm` (optional) | `BaseChatModel` | Any LangChain‑compatible chat model. If omitted, the package creates a `ChatLLM7` instance automatically. |
| `api_key` (optional) | `str` | API key for LLM7. If not supplied, the function reads `LLM7_API_KEY` from the environment. |

---

## Using a Custom LLM

You can pass any LangChain chat model (OpenAI, Anthropic, Google, …). Example with OpenAI:

```python
from langchain_openai import ChatOpenAI
from optimistic_pessimistic_evaluator import optimistic_pessimistic_evaluator

my_llm = ChatOpenAI(model="gpt-4o-mini")
report = optimistic_pessimistic_evaluator(user_input, llm=my_llm)
```

Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from optimistic_pessimistic_evaluator import optimistic_pessimistic_evaluator

my_llm = ChatAnthropic()
report = optimistic_pessimistic_evaluator(user_input, llm=my_llm)
```

Google Gemini:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from optimistic_pessimistic_evaluator import optimistic_pessimistic_evaluator

my_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
report = optimistic_pessimistic_evaluator(user_input, llm=my_llm)
```

---

## Default LLM (LLM7)

If you do not provide a custom model, the function uses **ChatLLM7** from the `langchain_llm7` package:

```python
from langchain_llm7 import ChatLLM7
```

The free tier of LLM7 offers generous rate limits for typical evaluation workloads.  
To use a custom key:

```python
report = optimistic_pessimistic_evaluator(user_input, api_key="YOUR_LLM7_API_KEY")
```

You can obtain a free API key by signing up at <https://token.llm7.io/>.

---

## Output

The function returns a `List[str]` containing the extracted data that matches the predefined regex pattern, e.g.:

```json
[
  "Optimistic approach is faster for low‑traffic scenarios.",
  "Pessimistic approach provides higher reliability under load."
]
```

If the LLM call fails or the output does not match the pattern, a `RuntimeError` is raised with the underlying error message.

---

## Contributing

Contributions are welcome! Feel free to open a pull request or submit an issue.

---

## Issues & Support

Report bugs or request features here: <https://github.com/chigwell/optimistic-pessimistic-evaluator/issues>

---

## Author

**Eugene Evstafev** – <hi@eugene.plus>  
GitHub: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License.