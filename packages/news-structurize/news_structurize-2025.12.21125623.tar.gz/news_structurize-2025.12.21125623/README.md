# news-structurize
[![PyPI version](https://badge.fury.io/py/news-structurize.svg)](https://badge.fury.io/py/news-structurize)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/news-structurize)](https://pepy.tech/project/news-structurize)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**news-structurize** is a lightweight Python package that transforms a news headline or a short text snippet into a structured summary. The output contains key elements such as the person involved, the event, and the financial or business impact. It leverages an LLM (by default **ChatLLM7**) together with regex‑based pattern matching to guarantee a consistent, machine‑readable format—perfect for automated news aggregation, financial reporting, or data‑extraction pipelines.

---

## Features

- **One‑function API** – just call `news_structurize()` with your text.
- **Built‑in LLM** – uses `ChatLLM7` from the `langchain_llm7` package out‑of‑the‑box.
- **Pluggable LLMs** – pass any LangChain‑compatible chat model (OpenAI, Anthropic, Google, …).
- **Regex‑validated output** – guarantees that the returned data matches the expected schema.
- **Zero‑configuration default** – works with the free tier of LLM7; optional API key handling.

---

## Installation

```bash
pip install news_structurize
```

---

## Quick Start

```python
from news_structurize import news_structurize

# Simple call – uses the default ChatLLM7 (needs LLM7_API_KEY in env or default key)
headline = "Apple CEO Tim Cook announces $2 billion investment in renewable energy"
summary = news_structurize(headline)

print(summary)
# Example output:
# ['Person: Tim Cook', 'Event: Investment announcement', 'Impact: $2 billion in renewable energy']
```

---

## Advanced Usage – Supplying Your Own LLM

You can provide any LangChain chat model that follows the `BaseChatModel` interface.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from news_structurize import news_structurize

llm = ChatOpenAI(model="gpt-4o-mini")
headline = "Tesla reports record Q3 deliveries"
summary = news_structurize(headline, llm=llm)

print(summary)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from news_structurize import news_structurize

llm = ChatAnthropic(model="claude-3-haiku-20240307")
headline = "Amazon expands grocery footprint with 15 new stores"
summary = news_structurize(headline, llm=llm)

print(summary)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from news_structurize import news_structurize

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
headline = "Microsoft acquires AI startup for $1.2 billion"
summary = news_structurize(headline, llm=llm)

print(summary)
```

---

## API Reference

```python
news_structurize(
    user_input: str,
    llm: Optional[BaseChatModel] = None,
    api_key: Optional[str] = None
) -> List[str]
```

| Parameter   | Type                         | Description |
|-------------|------------------------------|-------------|
| `user_input` | `str` | The news headline or short text snippet to be structured. |
| `llm`        | `Optional[BaseChatModel]` | A LangChain chat model instance. If omitted, the default `ChatLLM7` is used. |
| `api_key`    | `Optional[str]` | API key for LLM7. If omitted, the function looks for `LLM7_API_KEY` in the environment; otherwise a placeholder key (`"None"`) is used (suitable for the free tier). |

The function returns a list of strings, each representing a parsed element (e.g., `["Person: …", "Event: …", "Impact: …"]`). If the LLM call fails, a `RuntimeError` is raised with the underlying error message.

---

## Configuration & Rate Limits

- **LLM7 Free Tier** – Adequate for most development and low‑volume production use cases.
- **Higher Limits** – Obtain a personal API key by registering at https://token.llm7.io/ and set it via the environment variable `LLM7_API_KEY` or pass it directly to `news_structurize()`.

```bash
export LLM7_API_KEY="your_api_key_here"
```

---

## Contributing

Issues, feature requests, and pull requests are welcome! Please file them on the GitHub repository:

🔗 https://github....  

When contributing, follow standard Python packaging conventions and keep the public interface limited to the `news_structurize` function.

---

## License

This project is licensed under the MIT License.

---

## Author

**Eugene Evstafev**  
📧 Email: hi@euegne.plus  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## Acknowledgements

- **ChatLLM7** – the default language model, provided by the `langchain_llm7` package: https://pypi.org/project/langchain-llm7/
- **LangChain** – for the unified LLM interface and message handling.