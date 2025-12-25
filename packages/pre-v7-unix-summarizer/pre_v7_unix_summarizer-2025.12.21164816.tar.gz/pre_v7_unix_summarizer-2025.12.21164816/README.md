# pre‑v7‑unix‑summarizer
[![PyPI version](https://badge.fury.io/py/pre-v7-unix-summarizer.svg)](https://badge.fury.io/py/pre-v7-unix-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/pre-v7-unix-summarizer)](https://pepy.tech/project/pre-v7-unix-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package that processes text about early Unix history (pre‑V7) and returns concise, structured summaries. The summaries are generated via a language model and are forced to match a predefined XML‑like pattern, making them easy to parse and validate.

---

## Installation

```bash
pip install pre_v7_unix_summarizer
```

---

## Quick Start

```python
from pre_v7_unix_summarizer import pre_v7_unix_summarizer

# Simple call – the default ChatLLM7 will be used
summary = pre_v7_unix_summarizer(
    user_input="The early days of Unix started at AT&T Bell Labs in the late 1960s..."
)

print(summary)   # -> List of strings that match the output pattern
```

---

## Parameters

| Name       | Type                         | Description |
|------------|------------------------------|-------------|
| **user_input** | `str` | Raw text containing historical Unix information that you want to summarize. |
| **llm** | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the package creates a default `ChatLLM7` instance. |
| **api_key** | `Optional[str]` | API key for the LLM7 service. If not supplied, the function looks for the environment variable `LLM7_API_KEY`. If that is also missing, a placeholder key `"None"` is used. |

---

## Under the Hood

- **Default LLM** – `ChatLLM7` from the `langchain_llm7` package (see https://pypi.org/project/langchain-llm7/).
- **Pattern Matching** – The response is validated against a regular expression defined in `prompts.pattern` using `llmatch`. Only data that matches the pattern is returned.

---

## Using a Custom LLM

You can provide any LangChain‑compatible chat model. Below are a few examples.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from pre_v7_unix_summarizer import pre_v7_unix_summarizer

llm = ChatOpenAI()
summary = pre_v7_unix_summarizer(
    user_input="Your Unix text here...",
    llm=llm
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from pre_v7_unix_summarizer import pre_v7_unix_summarizer

llm = ChatAnthropic()
summary = pre_v7_unix_summarizer(
    user_input="Your Unix text here...",
    llm=llm
)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from pre_v7_unix_summarizer import pre_v7_unix_summarizer

llm = ChatGoogleGenerativeAI()
summary = pre_v7_unix_summarizer(
    user_input="Your Unix text here...",
    llm=llm
)
```

---

## API Key & Rate Limits

- **LLM7 Free Tier** – The default rate limits are sufficient for most research and hobbyist use cases.
- **Higher Limits** – Provide your own API key either through the `LLM7_API_KEY` environment variable or by passing `api_key="YOUR_KEY"` directly to the function.
- **Get a Free Key** – Register at https://token.llm7.io/ to obtain an API key.

---

## Contributing & Support

If you encounter any issues or have feature requests, please open an issue on GitHub:

https://github....  

We welcome contributions, bug reports, and suggestions.

---

## License

This project is licensed under the MIT License.

---

## Author

**Eugene Evstafev** – [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)