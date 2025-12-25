# VPSCompass
[![PyPI version](https://badge.fury.io/py/vpscompass.svg)](https://badge.fury.io/py/vpscompass)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vpscompass)](https://pepy.tech/project/vpscompass)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**VPSCompass** is a lightweight Python package that lets you quickly compare virtual private server (VPS) offerings from raw text inputs.  
Just paste a list of providers, plans, or key feature snippets and get a structured breakdown of pricing, performance, and trade‑offs in a single function call.

---

## Installation

```bash
pip install vpscompass
```

---

## Usage

```python
# Basic usage with the default LLM7 model
from vpscompass import vpscompass

user_input = """
Provider A: 1 vCPU, 2GB RAM, 50GB SSD, $10/month, 1TB bandwidth
Provider B: 2 vCPU, 4GB RAM, 100GB SSD, $20/month, 2TB bandwidth
"""

comparison = vpscompass(user_input)
print(comparison)
```

```
[
  "Provider A | 1 vCPU | 2GB RAM | 50GB SSD | $10 | 1TB bandwidth",
  "Provider B | 2 vCPU | 4GB RAM | 100GB SSD | $20 | 2TB bandwidth"
]
```

---

## Parameters

- **`user_input: str`**  
  The raw text that contains provider details.  
- **`llm: Optional[BaseChatModel]`**  
  Optional LangChain LLM instance. If omitted, the package falls back to `ChatLLM7` from `langchain_llm7`.  
- **`api_key: Optional[str]`**  
  API key for LLM7. If not supplied, the package looks for the `LLM7_API_KEY` environment variable, and finally defaults to `"None"` when no key is available.

---

## Swapping the Default LLM

You can provide any LangChain compatible model. Below are a few examples:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from vpscompass import vpscompass

llm = ChatOpenAI()
response = vpscompass(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from vpscompass import vpscompass

llm = ChatAnthropic()
response = vpscompass(user_input, llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vpscompass import vpscompass

llm = ChatGoogleGenerativeAI()
response = vpscompass(user_input, llm=llm)
```

---

## Rate Limits & API Keys

The default free tier of LLM7 comes with generous rate limits suitable for most use cases.  
If you need higher limits, just supply your own key:

```bash
export LLM7_API_KEY="YOUR_KEY"
```

or pass it directly:

```python
vpscompass(user_input, api_key="YOUR_KEY")
```

You can obtain a free key by registering at <https://token.llm7.io/>.

---

## Issues & Contributions

Have a bug or feature request? Open an issue on the GitHub repository.

> GitHub issues: <https://github.com/chigwell/vpscompass/>

---

## Author

- **Eugene Evstafev**  
- Email: <hi@euegne.plus>  
- GitHub: `<chigwell>`

---