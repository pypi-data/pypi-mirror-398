# geopolitex-analyzer
[![PyPI version](https://badge.fury.io/py/geopolitex-analyzer.svg)](https://badge.fury.io/py/geopolitex-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/geopolitex-analyzer)](https://pepy.tech/project/geopolitex-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**geopolitex-analyzer** is a lightweight Python package that turns short news headlines or text snippets about geopolitics, defense, and international competition into structured, LLM‑generated summaries. The output always follows a predefined pattern (subject, comparative context, implications) and is validated with robust regex matching to guarantee consistency and accuracy.

---

## Features

- **One‑line summarisation** for geopolitical and defense‑related texts.  
- **Pattern‑based validation** using `llmatch` to ensure the LLM output conforms to the expected format.  
- **Pluggable LLM backend** – defaults to `ChatLLM7` but works with any LangChain‑compatible chat model (OpenAI, Anthropic, Google, etc.).  
- Simple API: just pass the raw text and get a list of structured strings back.

---

## Installation

```bash
pip install geopolitex_analyzer
```

---

## Quick Start

```python
from geopolitex_analyzer import geopolitex_analyzer

# Simple usage with the default ChatLLM7 (requires an API key)
summary = geopolitex_analyzer(
    user_input="China launches a new hypersonic missile system, threatening regional stability."
)

print(summary)
# -> ['Subject: China...', 'Comparative Context: ...', 'Implications: ...']
```

### Using a custom LangChain LLM

You can provide any LangChain chat model that implements `BaseChatModel`. This is useful if you prefer OpenAI, Anthropic, Google Gemini, etc.

#### OpenAI example

```python
from langchain_openai import ChatOpenAI
from geopolitex_analyzer import geopolitex_analyzer

my_llm = ChatOpenAI(model="gpt-4o-mini")
summary = geopolitex_analyzer(
    user_input="Russia expands its naval presence in the Arctic.",
    llm=my_llm,
)

print(summary)
```

#### Anthropic example

```python
from langchain_anthropic import ChatAnthropic
from geopolitex_analyzer import geopolitex_analyzer

my_llm = ChatAnthropic(model="claude-3-haiku-20240307")
summary = geopolitex_analyzer(
    user_input="India announces a new defense budget focusing on AI‑driven weaponry.",
    llm=my_llm,
)

print(summary)
```

#### Google Gemini example

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from geopolitex_analyzer import geopolitex_analyzer

my_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
summary = geopolitex_analyzer(
    user_input="EU sanctions target new Russian aerospace firms.",
    llm=my_llm,
)

print(summary)
```

### Supplying an API key for the default LLM7 backend

If you rely on the built‑in `ChatLLM7` model, provide an API key either via the `LLM7_API_KEY` environment variable or directly:

```python
from geopolitex_analyzer import geopolitex_analyzer

summary = geopolitex_analyzer(
    user_input="Turkey acquires advanced drone technology from South Korea.",
    api_key="your_llm7_api_key_here",
)

print(summary)
```

A free API key can be obtained by registering at **https://token.llm7.io/**. The free tier’s rate limits are sufficient for most typical use cases.

---

## Function Reference

```python
geopolitex_analyzer(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| `user_input`| `str`                    | Raw headline or short text describing a geopolitical/defense topic. |
| `api_key`   | `Optional[str]`          | API key for the default `ChatLLM7`. If omitted, the function looks for the `LLM7_API_KEY` env var. |
| `llm`       | `Optional[BaseChatModel]`| Any LangChain chat model. If provided, it overrides the default `ChatLLM7`. |

**Return value:** A list of strings that match the defined output pattern (e.g., subject, comparative context, implications). If the LLM response does not satisfy the pattern, a `RuntimeError` is raised.

---

## Dependencies

- `llmatch_messages` – pattern‑matching helper used to enforce output format.  
- `langchain-core` – core interfaces for LLMs (`BaseChatModel`, message types).  
- `langchain-llm7` – wrapper for the LLM7 service (automatically installed).  
- `geopolitex-analyzer`’s own `prompts.py` (contains the system / human prompts and the regex pattern).

---

## Contributing & Support

- **Bug reports & feature requests:** https://github.com/chigwell/geopolitex_analyzer/issues  
- **Pull requests:** Contributions are welcome—please follow the standard GitHub workflow.

---

## Author

**Eugene Evstafev**  
Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

## License

MIT License – see the `LICENSE` file in the repository for details.

---  

*Happy analysing!*