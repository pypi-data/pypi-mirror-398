# keyinfostruct
[![PyPI version](https://badge.fury.io/py/keyinfostruct.svg)](https://badge.fury.io/py/keyinfostruct)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/keyinfostruct)](https://pepy.tech/project/keyinfostruct)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**keyinfostruct** is a lightweight Python package that extracts and structures key information from personal experience narratives (e.g., social‑media posts, messages).  
It automatically identifies the main points, emotions, and suggested actions from free‑form text using an LLM and returns the data in a ready‑to‑use list.

## Features

- One‑function API – just call `keyinfostruct(...)`.
- Works out‑of‑the‑box with **ChatLLM7** (default LLM).
- Plug‑and‑play with any LangChain‑compatible chat model (OpenAI, Anthropic, Google, etc.).
- Returns data that matches a strict regular‑expression pattern, guaranteeing predictable output.

## Installation

```bash
pip install keyinfostruct
```

## Quick Start

```python
from keyinfostruct import keyinfostruct

user_input = """
I just posted on Instagram that I'm getting divorced. 
Now I see a bot impersonating me and replying to my friends with weird messages.
I'm feeling angry and scared. 
What should I do?
"""

# Use the default ChatLLM7 (API key is read from env LLM7_API_KEY)
response = keyinfostruct(user_input)

print(response)
# Example output:
# [
#   "Event: announced divorce on Instagram",
#   "Emotion: angry, scared",
#   "Suggested Action: report impersonation, change passwords, inform friends"
# ]
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The raw text you want to analyse. |
| `llm` *(optional)* | `BaseChatModel` | Any LangChain chat model. If omitted, the package instantiates **ChatLLM7** automatically. |
| `api_key` *(optional)* | `str` | LLM7 API key. If not supplied, the function reads the environment variable `LLM7_API_KEY`. If that is also missing, a placeholder `"None"` is used (the request will fail unless you provide a real key). |

## Using Your Own LLM

You can swap the default model for any LangChain‑compatible chat model.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from keyinfostruct import keyinfostruct

llm = ChatOpenAI(model="gpt-4o-mini")
response = keyinfostruct(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from keyinfostruct import keyinfostruct

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = keyinfostruct(user_input, llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from keyinfostruct import keyinfostruct

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = keyinfostruct(user_input, llm=llm)
```

## API Key for LLM7

- **Free tier**: sufficient for most development and small‑scale usage.
- **Higher limits**: obtain an upgraded key from the LLM7 dashboard.

Set the key via environment variable:

```bash
export LLM7_API_KEY="your_llm7_api_key"
```

Or pass it directly:

```python
response = keyinfostruct(user_input, api_key="your_llm7_api_key")
```

Free keys are available after registration at <https://token.llm7.io/>.


## How It Works

`keyinfostruct` builds a LangChain message chain consisting of a system prompt, a human prompt (your `user_input`), and a regex pattern defined in `keyinfostruct.prompts`.  
The helper `llmatch` runs the LLM, validates the output against the pattern, and returns the extracted list. If the LLM response does not satisfy the pattern, a `RuntimeError` is raised.

## Contributing & Support

- **Issues & feature requests**: <https://github.com/chigwell/keyinfostruct/issues>
- **Pull requests** are welcome—please follow the repository’s contribution guidelines.

## License

This project is licensed under the MIT License.

## Author

**Eugene Evstafev**  
Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

*Happy structuring!*