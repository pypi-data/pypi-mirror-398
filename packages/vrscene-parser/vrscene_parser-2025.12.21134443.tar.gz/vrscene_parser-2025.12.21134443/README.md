# vrscene-parser
[![PyPI version](https://badge.fury.io/py/vrscene-parser.svg)](https://badge.fury.io/py/vrscene-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vrscene-parser)](https://pepy.tech/project/vrscene-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**vrscene-parser** is a lightweight Python package that transforms natural‑language descriptions of virtual‑reality (VR) scenes into a structured, validated format.  
It leverages an LLM (default **ChatLLM7**) to interpret the input text and ensures the output matches a predefined regular‑expression pattern, making the results consistent and ready for downstream processing (scene generation, tagging, metadata extraction, etc.).

---

## Installation

```bash
pip install vrscene_parser
```

---

## Quick Start

```python
from vrscene_parser import vrscene_parser

user_input = """
A futuristic city with neon lights, flying cars, and a large holographic billboard
displaying a rotating 3D logo in the center of the main square.
"""

# Use the default LLM (ChatLLM7). The API key is read from the environment variable LLM7_API_KEY.
response = vrscene_parser(user_input)

print(response)   # -> List of extracted data that matches the required pattern
```

---

## Function Signature

```python
def vrscene_parser(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| **user_input** | `str` | The free‑form description of a VR scene that you want to parse. |
| **api_key**   | `Optional[str]` | API key for **ChatLLM7**. If omitted, the function reads `LLM7_API_KEY` from the environment, or falls back to a default placeholder. |
| **llm**       | `Optional[BaseChatModel]` | Any LangChain‑compatible LLM instance. If omitted, the package creates a `ChatLLM7` instance automatically. |

---

## Using a Custom LLM

You can replace the default LLM with any LangChain chat model (e.g., OpenAI, Anthropic, Google Gemini). Just pass the model instance to `vrscene_parser`.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from vrscene_parser import vrscene_parser

my_llm = ChatOpenAI(model="gpt-4o-mini")
response = vrscene_parser(user_input, llm=my_llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from vrscene_parser import vrscene_parser

my_llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = vrscene_parser(user_input, llm=my_llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vrscene_parser import vrscene_parser

my_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = vrscene_parser(user_input, llm=my_llm)
```

---

## API Key for ChatLLM7

The default LLM is **ChatLLM7** from the `langchain_llm7` package (see https://pypi.org/project/langchain-llm7/).  
Free tier rate limits are sufficient for most development and testing scenarios.

- **Provide the key via environment variable**: `export LLM7_API_KEY="your_key_here"`
- **Or pass it directly**:

```python
response = vrscene_parser(user_input, api_key="your_key_here")
```

You can obtain a free API key by registering at https://token.llm7.io/.

---

## Error Handling

If the LLM response does **not** match the expected regular‑expression pattern, the function raises a `RuntimeError` with the underlying error message.

---

## Contributing & Support

* **Issues / feature requests**: <https://github.com/chigwell/vrscene_parser/issues>  
* **Pull requests** are welcome – please follow the standard GitHub workflow.

---

## Author

**Eugene Evstafev**  
✉️ Email: [hi@eugene.plus](mailto:hi@eugene.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.