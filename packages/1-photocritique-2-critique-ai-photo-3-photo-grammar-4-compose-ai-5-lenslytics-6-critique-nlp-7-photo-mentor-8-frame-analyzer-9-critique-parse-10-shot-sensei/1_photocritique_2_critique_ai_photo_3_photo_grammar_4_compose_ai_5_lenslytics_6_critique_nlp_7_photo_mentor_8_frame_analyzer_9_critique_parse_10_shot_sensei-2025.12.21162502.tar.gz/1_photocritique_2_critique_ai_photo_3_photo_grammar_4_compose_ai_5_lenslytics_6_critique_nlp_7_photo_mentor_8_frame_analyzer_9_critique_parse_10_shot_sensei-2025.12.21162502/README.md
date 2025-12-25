# 1‑photocritique — Automated Photo Critique Generator
[![PyPI version](https://badge.fury.io/py/1-photocritique-2-critique-ai-photo-3-photo-grammar-4-compose-ai-5-lenslytics-6-critique-nlp-7-photo-mentor-8-frame-analyzer-9-critique-parse-10-shot-sensei.svg)](https://badge.fury.io/py/1-photocritique-2-critique-ai-photo-3-photo-grammar-4-compose-ai-5-lenslytics-6-critique-nlp-7-photo-mentor-8-frame-analyzer-9-critique-parse-10-shot-sensei)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/1-photocritique-2-critique-ai-photo-3-photo-grammar-4-compose-ai-5-lenslytics-6-critique-nlp-7-photo-mentor-8-frame-analyzer-9-critique-parse-10-shot-sensei)](https://pepy.tech/project/1-photocritique-2-critique-ai-photo-3-photo-grammar-4-compose-ai-5-lenslytics-6-critique-nlp-7-photo-mentor-8-frame-analyzer-9-critique-parse-10-shot-sensei)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**1‑photocritique** is a lightweight Python package that takes a user‑provided textual description of a photograph and returns a structured critique covering composition, lighting, and subject matter.  
It uses pattern‑matching (`llmatch`) to enforce a consistent output format, making it ideal for photography enthusiasts, educators, or developers who need quick, automated feedback without manual review.

---

## Features

- **Single‑function API** – call one function with your text and get back a list of structured feedback strings.  
- **Out‑of‑the‑box LLM** – defaults to `ChatLLM7` (from the `langchain_llm7` package) with optional API‑key handling.  
- **LLM‑agnostic** – you can pass any LangChain‑compatible chat model (OpenAI, Anthropic, Google Gemini, etc.).  
- **Regex‑driven output** – ensures the returned critique always matches the expected pattern defined in `prompts.py`.  
- **No extra dependencies** beyond LangChain core, `llmatch_messages`, and the chosen LLM provider.

---

## Installation

```bash
pip install 1-photocritique
```

---

## Quick Start

```python
# Basic usage with the default LLM (ChatLLM7)
from 1_photocritique import pkg_1_photocritique

description = """
A portrait of a young woman standing near a window. The sunlight streams in,
casting soft shadows on her face. She is wearing a red scarf and looking
directly at the camera.
"""

critique = pkg_1_photocritique(
    user_input=description,
    api_key="YOUR_LLM7_API_KEY"   # optional – otherwise reads LLM7_API_KEY env var
)

print(critique)   # → List of structured feedback strings
```

### Using a custom LangChain LLM

You can safely provide any LangChain chat model that implements `BaseChatModel`.

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from 1_photocritique import pkg_1_photocritique

llm = ChatOpenAI(model="gpt-4o-mini")
critique = pkg_1_photocritique(user_input=description, llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from 1_photocritique import pkg_1_photocritique

llm = ChatAnthropic(model_name="claude-3-haiku-20240307")
critique = pkg_1_photocritique(user_input=description, llm=llm)
```

#### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from 1_photocritique import pkg_1_photocritique

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
critique = pkg_1_photocritique(user_input=description, llm=llm)
```

---

## API Reference

### `pkg_1_photocritique(user_input: str, api_key: Optional[str] = None, llm: Optional[BaseChatModel] = None) -> List[str]`

| Parameter | Type | Description |
|-----------|------|-------------|
| **user_input** | `str` | The textual description of the photo you want critiqued. |
| **api_key** | `Optional[str]` | API key for `ChatLLM7`. If omitted the function will read the `LLM7_API_KEY` environment variable or fallback to a placeholder `"None"` (which triggers a request‑failure). |
| **llm** | `Optional[BaseChatModel]` | A LangChain chat model. When `None`, the function creates a default `ChatLLM7` instance using `api_key`. |

**Returns**: `List[str]` – a list of feedback strings that match the regex pattern defined in `prompts.pattern`.

**Exceptions**: Raises `RuntimeError` if the LLM call fails or the response does not match the expected pattern.

---

## Configuration & Rate Limits

- **Default LLM** – `ChatLLM7` (free tier) offers generous rate limits for typical usage.  
- **Higher limits** – supply your own `api_key` (environment variable `LLM7_API_KEY` or the `api_key` argument). Get a free key at <https://token.llm7.io/>.  
- **Custom LLMs** – Pass any LangChain‑compatible model via the `llm` argument as shown above.

---

## Contributing

Feel free to open issues or submit pull requests on the repository.  
All contributions are welcome!

- **Issue tracker**: `/issues`  
- **Author**: Eugene Evstafev &lt;hi@euegne.plus&gt;  
- **GitHub**: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

--- 

*Happy shooting, and enjoy instant, AI‑powered critiques!*