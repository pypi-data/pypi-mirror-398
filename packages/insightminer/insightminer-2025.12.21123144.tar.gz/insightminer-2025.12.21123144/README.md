# insightminer
[![PyPI version](https://badge.fury.io/py/insightminer.svg)](https://badge.fury.io/py/insightminer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/insightminer)](https://pepy.tech/project/insightminer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**insightminer** is a lightweight Python package that extracts and structures key insights from opinionated articles, blog posts, tweets, and other short texts. It leverages the `llmatch‑messages` library together with a language model (LLM) to parse free‑form input into a predefined, regex‑validated structure, making downstream analysis (sentiment, trend tracking, etc.) straightforward and consistent.

---

## ✨ Features

- **One‑function interface** – Call `insightminer()` with your text and get a list of extracted fields.
- **Built‑in LLM** – Uses `ChatLLM7` from the `langchain_llm7` package by default (free tier suitable for most workloads).
- **Pluggable LLM** – Pass any LangChain‑compatible chat model (OpenAI, Anthropic, Google, etc.) if you prefer a different provider.
- **Regex‑driven pattern matching** – Guarantees that the output conforms to the pattern you define.
- **Simple installation** – Available on PyPI.

---

## 📦 Installation

```bash
pip install insightminer
```

---

## 🚀 Quick Start

```python
from insightminer import insightminer

user_input = "I Wouldn't Want John Solomon's New CMO Job at Mozilla"
results = insightminer(user_input)

print(results)
# Example output: ['John Solomon', 'new CMO job', 'Mozilla']
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| **user_input** | `str` | The text to be processed (e.g., a blog post title, tweet, etc.). |
| **llm** | `Optional[BaseChatModel]` | A LangChain chat model instance. If omitted, the default `ChatLLM7` is used. |
| **api_key** | `Optional[str]` | API key for LLM7. If omitted, the function reads the `LLM7_API_KEY` environment variable or falls back to the default key (`"None"`). |

---

## 🔧 Using a Custom LLM

You can safely replace the default `ChatLLM7` with any LangChain‑compatible chat model.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from insightminer import insightminer

llm = ChatOpenAI()
response = insightminer("Your text here", llm=llm)
print(response)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from insightminer import insightminer

llm = ChatAnthropic()
response = insightminer("Your text here", llm=llm)
print(response)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from insightminer import insightminer

llm = ChatGoogleGenerativeAI()
response = insightminer("Your text here", llm=llm)
print(response)
```

---

## 🔑 LLM7 API Key

- **Default behaviour**: The function looks for an environment variable `LLM7_API_KEY`.  
- **Providing manually**: Pass `api_key="YOUR_KEY"` when calling `insightminer`.  
- **Free tier**: Sufficient for typical usage of this package.  
- **Get a key**: Register for free at <https://token.llm7.io/>.

---

## 📚 Documentation & References

- **`ChatLLM7` package**: <https://pypi.org/project/langchain-llm7/>  
- **LangChain LLM documentation**: <https://python.langchain.com/docs/>  

---

## 🐞 Issues & Contributions

If you encounter bugs or have feature requests, please open an issue:

<https://github....>

Pull requests are welcome! Follow the standard GitHub workflow and ensure tests (if any) pass before submitting.

---

## ✉️ Author

**Eugene Evstafev** – <hi@euegne.plus>  
GitHub: [chigwell](https://github.com/chigwell)

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.