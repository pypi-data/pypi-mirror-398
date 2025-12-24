# news-summerizer

[![PyPI version](https://img.shields.io/pypi/v/news-summerizer.svg)](https://pypi.org/project/news-summerizer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/news-summerizer.svg)](https://pypistats.org/packages/news-summerizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Eugene%20Evstafev-blue.svg)](https://www.linkedin.com/in/eugeneevstafev/)

A lightweight Python package that turns concise news headlines or short snippets into **structured summaries** in a simple XML‑like format.  
The output is well‑defined and machine‑readable, making the data usable for news aggregation, content tagging, or quick briefing generation.

## Features

- Extract key facts from a headline or short text: **event, location, involved parties, significance**.
- Output is constrained by a regular expression so the result is always predictable.
- Works with any LangChain `BaseChatModel`, falling back to the default LLM7 model.
- Zero‑configuration: install once, drop into any project and call `news_summerizer`.

## Installation

```bash
pip install news_summerizer
```

## Quick Example

```python
from news_summerizer import news_summerizer

user_input = (
    "Tesla's new Gigafactory in Austin expands production capacity for the Model 3 "
    "and the new Cybertruck, boosting U.S. manufacturing jobs."
)

summary = news_summerizer(user_input)
print(summary)
# [
#   "<summary>",
#   "  <event>Expanding production capacity</event>",
#   "  <location>Austin</location>",
#   "  <parties>Tesla, Model 3, Cybertruck</parties>",
#   "  <significance>Boosts U.S. manufacturing jobs</significance>",
#   "</summary>"
# ]
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The headline or news snippet to process. |
| `llm` | `Optional[BaseChatModel]` | A LangChain chat model instance.  If omitted, the package automatically creates a `ChatLLM7` instance. |
| `api_key` | `Optional[str]` | LLM7 API key.  If not supplied, the package looks for the `LLM7_API_KEY` environment variable, otherwise defaults to the free tier key (`"None"`). |

## Custom LLMs

`news_summerizer` works with any LangChain model.  Simply pass your own model instance:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from news_summerizer import news_summerizer

llm = ChatOpenAI()
summary = news_summerizer(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from news_summerizer import news_summerizer

llm = ChatAnthropic()
summary = news_summerizer(user_input, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from news_summerizer import news_summerizer

llm = ChatGoogleGenerativeAI()
summary = news_summerizer(user_input, llm=llm)
```

## LLM7 API Key

The default free tier of LLM7 is usually sufficient.  For higher rate limits:

- Set the `LLM7_API_KEY` environment variable, or
- Pass the key directly: `news_summerizer(user_input, api_key="your_api_key")`

Free API keys can be obtained by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Project Links

- GitHub: https://github.com/chigwell/news-summerizer
- Issues: https://github.com/chigwell/news-summerizer/issues

---

### Author

Eugene Evstafev  
📧 hi@euegne.plus  
👤 [LinkedIn](https://www.linkedin.com/in/eugeneevstafev/)

--- 
**License**: MIT  
**Version**: 0.1.0 (check PyPI for the latest release)