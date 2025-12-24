# scamp-analyzer
[![PyPI version](https://badge.fury.io/py/scamp-analyzer.svg)](https://badge.fury.io/py/scamp-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/scamp-analyzer)](https://pepy.tech/project/scamp-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**scamp-analyzer** is a lightweight Python package that evaluates user‑provided text descriptions of mischievous or cleverly unconventional behavior (a “scamp” scenario). It returns a structured XML‑like assessment of the act’s creativity, humor, and potential social impact, categorizing it as *harmless fun*, *borderline*, or *potentially problematic*.

---

## Installation

```bash
pip install scamp_analyzer
```

---

## Quick Start

```python
from scamp_analyzer import scamp_analyzer

# Simple usage with the default LLM (ChatLLM7)
result = scamp_analyzer(
    user_input="I swapped the sugar with salt in the office kitchen."
)

print(result)   # → List of extracted XML‑like tags
```

### Parameters

| Name        | Type                     | Description |
|-------------|--------------------------|-------------|
| `user_input`| `str`                    | The text description of the scamp scenario to be analysed. |
| `llm`       | `Optional[BaseChatModel]`| A LangChain chat model. If omitted, the built‑in `ChatLLM7` is used. |
| `api_key`   | `Optional[str]`          | API key for LLM7. If omitted, the function reads `LLM7_API_KEY` from the environment (or uses a placeholder). |

---

## Using a Custom LLM

You can provide any LangChain chat model that implements `BaseChatModel`. Below are a few examples.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from scamp_analyzer import scamp_analyzer

llm = ChatOpenAI()
response = scamp_analyzer(
    user_input="I printed the boss's email signature on a birthday cake.",
    llm=llm
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from scamp_analyzer import scamp_analyzer

llm = ChatAnthropic()
response = scamp_analyzer(
    user_input="I replaced the office chairs with beanbags for a surprise.",
    llm=llm
)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from scamp_analyzer import scamp_analyzer

llm = ChatGoogleGenerativeAI()
response = scamp_analyzer(
    user_input="I swapped the ‘Out of Office’ replies with a funny poem.",
    llm=llm
)
```

---

## Default LLM (ChatLLM7)

If you don’t supply a custom `llm`, **scamp_analyzer** automatically creates a `ChatLLM7` instance:

```python
from scamp_analyzer import scamp_analyzer

response = scamp_analyzer(
    user_input="I anonymously left motivational sticky notes around the office."
)
```

* `ChatLLM7` is provided by the **langchain_llm7** package: https://pypi.org/project/langchain-llm7/
* The free tier’s rate limits are sufficient for typical usage.

### Providing Your Own LLM7 API Key

You can either set the environment variable:

```bash
export LLM7_API_KEY="your_llm7_api_key"
```

or pass it directly:

```python
response = scamp_analyzer(
    user_input="I organized a surprise flash mob at lunch.",
    api_key="your_llm7_api_key"
)
```

Obtain a free API key by registering at https://token.llm7.io/.

---

## Contributing & Issues

If you encounter any problems or have feature requests, please open an issue:

👉 https://github....  

We welcome contributions, documentation improvements, and bug fixes.

---

## Author

**Eugene Evstafev**  
📧 [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.