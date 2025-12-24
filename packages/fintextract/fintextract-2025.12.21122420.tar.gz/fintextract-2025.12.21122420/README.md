# fintextract
[![PyPI version](https://badge.fury.io/py/fintextract.svg)](https://badge.fury.io/py/fintextract)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/fintextract)](https://pepy.tech/project/fintextract)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**fintextract** is a lightweight Python package that extracts and structures key financial and business insights from unstructured news text.  
Give it a raw news sentence and receive a clear, machine‑readable summary containing:

- **Subject** – the main person or organization  
- **Key figures** – monetary amounts, percentages, etc.  
- **Significant event** – the core business event described  

Designed for financial analysts, business reporters, and investors who need to quickly parse breaking news.

---

## Features

- One‑function API (`fintextract`) that returns a list of extracted data items.  
- Built‑in default LLM: **ChatLLM7** (via the `langchain_llm7` integration).  
- Seamless integration with any LangChain‑compatible LLM (OpenAI, Anthropic, Google, …).  
- Simple regex‑based output validation ensures the response matches the expected pattern.  

---

## Installation

```bash
pip install fintextract
```

---

## Quick Start

```python
from fintextract import fintextract

news = "Elon Musk becomes first person worth $700B following pay package ruling."

result = fintextract(user_input=news)

print(result)
# Example output:
# ['Subject: Elon Musk', 'Key figure: $700B', 'Event: pay package ruling']
```

---

## API Reference

```python
def fintextract(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| **user_input** | `str` | The raw news text you want to analyze. |
| **api_key**    | `Optional[str]` | API key for **ChatLLM7**. If omitted, the function reads `LLM7_API_KEY` from the environment. |
| **llm**        | `Optional[BaseChatModel]` | A LangChain LLM instance. If not provided, the default `ChatLLM7` is instantiated automatically. |

The function returns a list of strings that match the pre‑defined output pattern (subject, key figure, event).  

---

## Using a Custom LLM

If you prefer another language model, simply pass a LangChain LLM instance:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from fintextract import fintextract

llm = ChatOpenAI()
response = fintextract(user_input="Your news text", llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from fintextract import fintextract

llm = ChatAnthropic()
response = fintextract(user_input="Your news text", llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from fintextract import fintextract

llm = ChatGoogleGenerativeAI()
response = fintextract(user_input="Your news text", llm=llm)
```

Any LangChain‑compatible `BaseChatModel` can be used in the same way.

---

## API Key & Rate Limits

- **ChatLLM7** (the default) uses the free tier rate limits, which are sufficient for typical usage.  
- To obtain a free API key, register at **[https://token.llm7.io/](https://token.llm7.io/)**.  
- Set the key via the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = fintextract(user_input="Your news text", api_key="YOUR_API_KEY")
```

If higher limits are needed, upgrade your LLM7 plan accordingly.

---

## Contributing

Contributions, bug reports, and feature requests are welcome!  
Please open an issue or submit a pull request on GitHub:

**Issues:** https://github.com/chigwell/fintextract/issues  

**Pull Requests:** https://github.com/chigwell/fintextract/pulls  

---

## License

This project is licensed under the MIT License.

---

## Author

**Eugene Evstafev** – [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

## Acknowledgements

- **ChatLLM7** integration from the `langchain_llm7` package – [https://pypi.org/project/langchain-llm7/](https://pypi.org/project/langchain-llm7/)  
- Pattern matching powered by `llmatch_messages.llmatch`.  

--- 

*Happy extracting!*