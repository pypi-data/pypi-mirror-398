# eventlytics-summarizer
[![PyPI version](https://badge.fury.io/py/eventlytics-summarizer.svg)](https://badge.fury.io/py/eventlytics-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/eventlytics-summarizer)](https://pepy.tech/project/eventlytics-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**eventlytics-summarizer** is a tiny Python package that wraps a language‑model call with pattern‑matching and retry logic, making it easy to get concise, structured summaries and key‑point extractions from free‑form event descriptions.  
It is especially suited for incident reports, news snippets, or any narrative that needs to be turned into a predictable, machine‑readable format.

## Installation

```bash
pip install eventlytics_summarizer
```

## Quick start

```python
from eventlytics_summarizer import eventlytics_summarizer

text = """
Gloria Ramirez, a 31‑year‑old patient at the emergency department, suddenly began
seizing and emitting a strange, oily odor.  Shortly after, several staff members
lost consciousness.  The incident was later attributed to a toxic reaction to a
medication administered to Ms. Ramirez.
"""

summary = eventlytics_summarizer(user_input=text)
print(summary)
# -> ['...']   # a list of strings that match the defined output pattern
```

## API

```python
eventlytics_summarizer(
    user_input: str,
    llm: Optional[BaseChatModel] = None,
    api_key: Optional[str] = None
) -> List[str]
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| **user_input** | `str` | The raw narrative you want to summarize / extract. |
| **llm**        | `BaseChatModel` (optional) | Any LangChain‑compatible chat model. If omitted, the package creates a `ChatLLM7` instance automatically. |
| **api_key**   | `str` (optional) | API key for LLM7. If not supplied, the function looks for the `LLM7_API_KEY` environment variable, falling back to a placeholder `"None"` (which triggers the default free‑tier limits). |

## Default LLM (LLM7)

If you do not provide your own model, `eventlytics_summarizer` uses **ChatLLM7** from the `langchain_llm7` package:

```python
from langchain_llm7 import ChatLLM7
```

The free tier of LLM7 provides enough calls for typical usage. To increase limits, supply your own API key:

```python
summary = eventlytics_summarizer(user_input=text, api_key="YOUR_LLM7_API_KEY")
```

You can obtain a free key by registering at <https://token.llm7.io/>.

## Using a custom LLM

You can plug any LangChain chat model that implements `BaseChatModel`. Below are a few common examples.

### OpenAI (ChatGPT)

```python
from langchain_openai import ChatOpenAI
from eventlytics_summarizer import eventlytics_summarizer

llm = ChatOpenAI(model="gpt-4o-mini")  # or any other OpenAI model
summary = eventlytics_summarizer(user_input=text, llm=llm)
```

### Anthropic (Claude)

```python
from langchain_anthropic import ChatAnthropic
from eventlytics_summarizer import eventlytics_summarizer

llm = ChatAnthropic(model="claude-3-haiku-20240307")
summary = eventlytics_summarizer(user_input=text, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from eventlytics_summarizer import eventlytics_summarizer

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
summary = eventlytics_summarizer(user_input=text, llm=llm)
```

## How it works

1. **Prompt construction** – a system prompt guides the model to produce concise, domain‑appropriate output, while a human prompt injects your `user_input`.
2. **Pattern matching** – the expected output format is described by a regular expression (`eventlytics_summarizer.prompts.pattern`). The response is validated against this regex.
3. **Retry / error handling** – `llmatch` automatically retries on mismatches and surfaces a clear `RuntimeError` if the model cannot satisfy the pattern.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License.

## Author

**Eugene Evstafev** – <hi@eugene.plus>  
GitHub: [chigwell](https://github.com/chigwell)

## Bugs & feature requests

If you encounter any problems or have ideas for improvement, please file an issue at:  
<https://github.com/chigwell/eventlytics-summarizer/issues>