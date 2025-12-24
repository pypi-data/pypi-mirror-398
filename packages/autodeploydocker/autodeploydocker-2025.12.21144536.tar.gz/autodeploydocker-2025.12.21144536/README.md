# autodeploydocker
[![PyPI version](https://badge.fury.io/py/autodeploydocker.svg)](https://badge.fury.io/py/autodeploydocker)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/autodeploydocker)](https://pepy.tech/project/autodeploydocker)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**autodeploydocker** is a tiny Python package that makes it easy to automate the deployment of Docker and Docker‑Compose applications to remote servers.  
It drives a language model (LLM) to generate the exact deployment steps, ensuring zero‑downtime deployments without the need for manual configuration changes.

---

## Installation

```bash
pip install autodeploydocker
```

---

## Quick start

```python
from autodeploydocker import autodeploydocker

# Minimal usage – the package will create a ChatLLM7 instance for you.
response = autodeploydocker(
    user_input="Deploy the latest version of my web‑app using Docker Compose on server X."
)

print(response)   # -> list of strings extracted from the LLM response
```

---

## Function signature

```python
def autodeploydocker(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
    ...
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| **user_input** | `str` | The natural‑language description of the deployment you want to perform. |
| **api_key**    | `Optional[str]` | API key for the default **ChatLLM7** backend. If omitted, the function reads `LLM7_API_KEY` from the environment. |
| **llm**        | `Optional[BaseChatModel]` | A LangChain‑compatible LLM instance. If provided, it overrides the default ChatLLM7. |

---

## How it works

The function builds a system prompt (`system_prompt`) and a human prompt (`human_prompt`) and sends them to the selected LLM.  
The LLM’s output is then validated against a regular‑expression pattern defined in `prompts.pattern`.  
If the output matches, the extracted data (a `List[str]`) is returned; otherwise a `RuntimeError` is raised.

---

## Using a custom LLM

You can safely supply any LangChain LLM that follows the `BaseChatModel` interface.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from autodeploydocker import autodeploydocker

llm = ChatOpenAI(model="gpt-4o")   # configure as you need
response = autodeploydocker(
    user_input="Deploy the staging environment with Docker Compose.",
    llm=llm,
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from autodeploydocker import autodeploydocker

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
response = autodeploydocker(
    user_input="Roll out a new version of the API service.",
    llm=llm,
)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from autodeploydocker import autodeploydocker

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
response = autodeploydocker(
    user_input="Update the production stack using Docker Compose.",
    llm=llm,
)
```

---

## Default LLM – ChatLLM7

If you do **not** pass an `llm` instance, `autodeploydocker` falls back to **ChatLLM7** from the `langchain_llm7` package:

```text
pip install langchain_llm7
```

ChatLLM7 works out‑of‑the‑box with a free tier that is sufficient for most use cases.  
To use a personal key, set the environment variable `LLM7_API_KEY` or pass the key directly:

```python
response = autodeploydocker(
    user_input="Deploy …",
    api_key="my-llm7-key",
)
```

You can obtain a free API key by registering at https://token.llm7.io/.

---

## Contributing & Support

If you encounter any issues, have a feature request, or want to contribute, please open an issue on GitHub:

https://github....  

---

## Author

**Eugene Evstafev** – [chigwell](https://github.com/chigwell)  
✉️ Email: hi@euegne.plus  

---

## License

This project is licensed under the MIT License.