# giftparcelstruct
[![PyPI version](https://badge.fury.io/py/giftparcelstruct.svg)](https://badge.fury.io/py/giftparcelstruct)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/giftparcelstruct)](https://pepy.tech/project/giftparcelstruct)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**giftparcelstruct** is a tiny Python package that takes a user‑written description of a gift‑wrapped parcel and returns a structured analysis of its contents, wrapping quality, and any hidden surprises.  
It uses pattern matching to ensure the LLM’s output follows a strict regex format, making it ideal for party games, event planning, creative writing prompts, or any scenario where you want to generate or guess parcel details in a fun, interactive way.

---

## Installation

```bash
pip install giftparcelstruct
```

---

## Quick Start

```python
from giftparcelstruct import giftparcelstruct

user_input = """
I received a bright red box wrapped in glossy paper with a silver bow.
Inside there was a small wooden puzzle, a scented candle, and a handwritten note.
"""

# Use the default LLM (ChatLLM7)
result = giftparcelstruct(user_input)

print(result)
```

**Output** – a list of strings matching the predefined pattern, e.g.:

```python
[
    "Wrapping: glossy, red, silver bow",
    "Contents: wooden puzzle, scented candle, handwritten note",
    "Surprise: hidden chocolate inside the puzzle"
]
```

---

## Function Signature

```python
giftparcelstruct(
    user_input: str,
    llm: Optional[BaseChatModel] = None,
    api_key: Optional[str] = None,
) -> List[str]
```

| Parameter   | Type                         | Description |
|------------|------------------------------|-------------|
| `user_input` | `str` | The free‑form text describing the parcel that you want to analyse. |
| `llm`        | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the package automatically creates a `ChatLLM7` instance. |
| `api_key`    | `Optional[str]` | API key for LLM7. If omitted, the function looks for the environment variable `LLM7_API_KEY`. If that is also missing, a placeholder value is used and the request will fail unless a real key is supplied. |

---

## Using a Custom LLM

You can plug any LangChain‑compatible chat model instead of the default `ChatLLM7`.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from giftparcelstruct import giftparcelstruct

llm = ChatOpenAI(model="gpt-4o-mini")
response = giftparcelstruct(user_input, llm=llm)
print(response)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from giftparcelstruct import giftparcelstruct

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = giftparcelstruct(user_input, llm=llm)
print(response)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from giftparcelstruct import giftparcelstruct

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = giftparcelstruct(user_input, llm=llm)
print(response)
```

---

## Default LLM – ChatLLM7

If you do not provide an `llm` argument, **giftparcelstruct** automatically creates a `ChatLLM7` instance from the **langchain‑llm7** package:

```python
from langchain_llm7 import ChatLLM7
```

*Package:* https://pypi.org/project/langchain-llm7  

The free tier of LLM7 offers generous rate limits that are sufficient for most hobby and prototype uses.

### Supplying an API Key

You can set the LLM7 key in the environment:

```bash
export LLM7_API_KEY="your_api_key_here"
```

Or pass it directly:

```python
response = giftparcelstruct(user_input, api_key="your_api_key_here")
```

Get a free API key by registering at https://token.llm7.io/.

---

## Contributing & Support

If you encounter any bugs or have feature requests, please open an issue:

https://github.com/chigwell/giftparcelstruct/issues

Pull requests and suggestions are very welcome!

---

## License

This project is licensed under the MIT License.

---

## Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)