# idea‑distiller
[![PyPI version](https://badge.fury.io/py/idea-distiller.svg)](https://badge.fury.io/py/idea-distiller)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/idea-distiller)](https://pepy.tech/project/idea-distiller)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**idea‑distiller** is a tiny utility package that extracts a concise, neutral summary of the core problem addressed by unconventional or controversial business and social initiatives.  
It leverages a language model (LLM) to focus on the “problem statement” of the input text while stripping away technical details, implementation specifics, and sensitive content.

---

## Installation

```bash
pip install idea_distiller
```

---

## Quick start

```python
from idea_distiller import idea_distiller

# Raw description of an initiative
user_input = """
In 2012 a program hired homeless people to become mobile Wi‑Fi hotspots,
providing free internet in public places while giving them a source of
income.
"""

# Get the distilled summary
summary = idea_distiller(user_input)

print(summary)
# → ['Problem: Lack of free public internet access and unemployment among homeless individuals.']
```

---

## Function signature

```python
def idea_distiller(
    user_input: str,
    llm: Optional[BaseChatModel] = None,
    api_key: Optional[str] = None,
) -> List[str]:
```

| Parameter   | Type                              | Description |
|-------------|-----------------------------------|-------------|
| **user_input** | `str` | The raw text describing the initiative you want to distill. |
| **llm** | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the package creates a `ChatLLM7` instance automatically. |
| **api_key** | `Optional[str]` | API key for the default **ChatLLM7** service. If not supplied, the environment variable `LLM7_API_KEY` is used. |

The function returns a list of strings that match the validation pattern defined in the package (normally a single concise sentence).

---

## Using a custom LLM

You can plug any LangChain‑compatible chat model instead of the default `ChatLLM7`.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from idea_distiller import idea_distiller

llm = ChatOpenAI(model="gpt-4o-mini")
response = idea_distiller(user_input, llm=llm)
print(response)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from idea_distiller import idea_distiller

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = idea_distiller(user_input, llm=llm)
print(response)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from idea_distiller import idea_distiller

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = idea_distiller(user_input, llm=llm)
print(response)
```

---

## API key & rate limits (default LLM7)

- The **free tier** of LLM7 provides enough quota for most development and low‑volume use cases.  
- To obtain a free API key, register at: <https://token.llm7.io/>.  
- You can supply the key directly:

```python
response = idea_distiller(user_input, api_key="YOUR_LLM7_API_KEY")
```

- Or set the environment variable beforehand:

```bash
export LLM7_API_KEY="YOUR_LLM7_API_KEY"
```

If higher rate limits are required, upgrade your LLM7 plan on the provider’s website.

---

## Contributing & Support

- **Issues & feature requests:** <https://github.com/chigwell/idea_distiller/issues>
- **Pull requests:** Welcome! Please follow the contributor guidelines in the repository.

---

## Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.