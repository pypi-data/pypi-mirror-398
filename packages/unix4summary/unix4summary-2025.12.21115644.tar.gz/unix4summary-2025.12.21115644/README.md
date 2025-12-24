# unix4summary
[![PyPI version](https://badge.fury.io/py/unix4summary.svg)](https://badge.fury.io/py/unix4summary)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/unix4summary)](https://pepy.tech/project/unix4summary)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`unix4summary` is a lightweight Python package that extracts structured summaries and key information from textual prompts related to **Unix Fourth Edition**.  
It parses user inputs—such as command descriptions, system behaviours, or feature overviews—and returns concise, well‑formatted details (e.g., command syntax, explanations, or expected outputs).  
The tool relies on regular‑expression matching and a retry mechanism to guarantee consistent return formats, making it ideal for quick reference or documentation generation without handling multimedia content.

---

## Table of Contents
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Custom Language Model](#custom-language-model)
  - [OpenAI](#openai)
  - [Anthropic](#anthropic)
  - [Google Gemini](#google-gemini)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Installation

```bash
pip install unix4summary
```

---

## Basic Usage

```python
from unix4summary import unix4summary

user_input = """
Explain the `exec` system call in Unix 4th Edition.
Provide the syntax and typical use cases.
"""

# Use the default LLM7 model
summary = unix4summary(user_input)

print(summary)
```

> *Output (example)*  
> ```
> [
>   "- Syntax: execve(const char *pathname, char *const argv[], char *const envp[])",
>   "- Purpose: Replaces the current process image with a new process image.",
>   "- Typical Usage: Executing a shell program from a custom script."
> ]
> ```

---

## Custom Language Model

`unix4summary` uses **ChatLLM7** (from `langchain_llm7`) by default.  
You can provide any LangChain `BaseChatModel` instance to switch providers.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from unix4summary import unix4summary

llm = ChatOpenAI()

response = unix4summary(user_input, llm=llm)
print(response)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from unix4summary import unix4summary

llm = ChatAnthropic()

response = unix4summary(user_input, llm=llm)
print(response)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from unix4summary import unix4summary

llm = ChatGoogleGenerativeAI()

response = unix4summary(user_input, llm=llm)
print(response)
```

> **Tip**: If you prefer to keep using the default ChatLLM7 but need higher rate limits, set an API key via the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = unix4summary(user_input, api_key="YOUR_LLM7_TOKEN")
```

You can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/).

---

## Configuration Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Text to process (Unix 4th Edition related command or concept). |
| `llm` | `Optional[BaseChatModel]` | LangChain language‑model instance. If omitted, `ChatLLM7` is used. |
| `api_key` | `Optional[str]` | API key for LLM7; read from `LLM7_API_KEY` env variable by default. |

---

## Contributing

Issues and pull requests are welcome!  
- Issues: [https://github.com/chigwell/unix4summary/issues](https://github.com/chigwell/unix4summary/issues)

---

## License

MIT © Eugene Evstafev

---

## Author

- **Eugene Evstafev**  
  Email: hi@euegne.plus  
  GitHub: [chigwell](https://github.com/chigwell)