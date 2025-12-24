# textsummarizer-llm

[![PyPI version](https://img.shields.io/pypi/v/textsummarizer-llm.svg)](https://pypi.org/project/textsummarizer-llm/)
[![License: MIT](https://img.shields.io/github/license/chigwell/textsummarizer-llm)](https://github.com/chigwell/textsummarizer-llm/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/textsummarizer-llm.svg)](https://pypi.org/project/textsummarizer-llm/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?logo=linkedin)](https://www.linkedin.com/in/eugene-evstafev)

## Overview

`textsummarizer_llm` provides a simple, pattern‑validated summarization utility powered by a language model (LLM).  
Given a raw text input (e.g., a headline, article excerpt, or description), the package:

* Sends the text to a chat LLM using **LangChain** messages.
* Enforces a predefined output format via a regular‑expression pattern (`llmatch`).
* Returns a list of extracted, structured summaries.

Typical use‑cases include content moderation, topic tagging, and automated summarization where a consistent response format is required.

## Installation

```bash
pip install textsummarizer_llm
```

## Quick Start

```python
from textsummarizer_llm import textsummarizer_llm

# Simple call – uses the default ChatLLM7 internally
summary = textsummarizer_llm(
    user_input="OpenAI just released GPT‑4 Turbo, offering faster inference and lower cost."
)

print(summary)   # → ['...structured summary according to the defined pattern...']
```

## Advanced Usage – Plugging Your Own LLM

You can pass any LangChain‑compatible chat model (e.g., OpenAI, Anthropic, Google) to the function.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from textsummarizer_llm import textsummarizer_llm

my_llm = ChatOpenAI(model="gpt-4o-mini")
result = textsummarizer_llm(
    user_input="A new study shows that daily meditation improves mental health.",
    llm=my_llm
)
print(result)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from textsummarizer_llm import textsummarizer_llm

anthropic_llm = ChatAnthropic(model="claude-3-sonnet-20240229")
result = textsummarizer_llm(
    user_input="The city council approved a new bike‑lane network.",
    llm=anthropic_llm
)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from textsummarizer_llm import textsummarizer_llm

google_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
result = textsummarizer_llm(
    user_input="Tesla announced a new battery technology with higher energy density.",
    llm=google_llm
)
```

## API Reference

```python
def textsummarizer_llm(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]:
    """
    Summarize `user_input` while ensuring the output matches a predefined regex pattern.

    Parameters
    ----------
    user_input: str
        The raw text that needs to be processed and summarized.
    api_key: Optional[str]
        API key for the default `ChatLLM7`. If omitted, the function first looks for the
        `LLM7_API_KEY` environment variable, then falls back to a placeholder key.
    llm: Optional[BaseChatModel]
        A LangChain chat model instance. If not provided, `ChatLLM7` from
        `langchain_llm7` is instantiated automatically.

    Returns
    -------
    List[str]
        A list of extracted summary strings that conform to the regex pattern.
    """
```

## Authentication & Rate Limits

The default LLM is **ChatLLM7** from the `langchain_llm7` package.  
Free‑tier limits are sufficient for typical development and small‑scale usage.  
If you require higher limits, provide your own API key:

```bash
export LLM7_API_KEY="your-llm7-api-key"
```

or directly:

```python
summary = textsummarizer_llm(
    user_input="...", 
    api_key="your-llm7-api-key"
)
```

You can obtain a free key at https://token.llm7.io/.

## Contributing

Contributions are welcome! Please open issues or pull requests on the GitHub repository.

## License

This project is licensed under the MIT License.

## Author

**Eugene Evstafev** – <hi@eugene.plus>  
GitHub: [chigwell](https://github.com/chigwell)

## Issues

Report bugs or request features via the issue tracker:  
https://github.com/chigwell/textsummarizer-llm/issues