# sciextractai
[![PyPI version](https://badge.fury.io/py/sciextractai.svg)](https://badge.fury.io/py/sciextractai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/sciextractai)](https://pepy.tech/project/sciextractai)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**sciextractai** – a lightweight Python package that extracts and structures key scientific insights from complex texts.  
It is especially useful for fast‑moving fields like attoscience where researchers need concise, structured summaries of breakthroughs, methods, and theories.

---

## 📦 Installation

```bash
pip install sciextractai
```

---

## 🚀 Quick Start

```python
from sciextractai import sciextractai

# Example scientific text (e.g., a recent attoscience paper)
user_input = """
Scientists have generated the shortest light pulse ever recorded, lasting only 3 attoseconds.
This breakthrough opens new possibilities for probing electron dynamics in atoms.
"""

# Call the extractor (defaults to ChatLLM7)
extracted_data = sciextractai(user_input)

print(extracted_data)
```

**Output**

A list of strings that match the extraction pattern defined in the package, e.g.:

```
[
    "Shortest light pulse: 3 attoseconds",
    "Implication: Probing electron dynamics in atoms"
]
```

---

## 🛠️ Function Signature

```python
def sciextractai(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]:
```

| Parameter   | Type                     | Description |
|------------|--------------------------|-------------|
| `user_input` | `str`                    | The scientific text you want to process. |
| `llm`       | `Optional[BaseChatModel]`| A LangChain LLM instance to use. If omitted, the package creates a default `ChatLLM7` instance. |
| `api_key`   | `Optional[str]`          | API key for **ChatLLM7**. If omitted, the function looks for the environment variable `LLM7_API_KEY`. |

---

## 🔧 Default LLM (ChatLLM7)

If you don’t provide an `llm` argument, `sciextractai` will instantiate **ChatLLM7** from the `langchain_llm7` package:

```python
from langchain_llm7 import ChatLLM7

resolved_llm = ChatLLM7(api_key=api_key, base_url="https://api.llm7.io/v1")
```

- **Installation:** `pip install langchain-llm7`
- **Documentation:** https://pypi.org/project/langchain-llm7/

---

## 🌟 Using a Custom LLM

You can pass any LangChain‑compatible LLM (e.g., OpenAI, Anthropic, Google Gemini).

### OpenAI

```python
from langchain_openai import ChatOpenAI
from sciextractai import sciextractai

llm = ChatOpenAI(model="gpt-4o-mini")
response = sciextractai(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from sciextractai import sciextractai

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = sciextractai(user_input, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from sciextractai import sciextractai

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = sciextractai(user_input, llm=llm)
```

---

## 🔑 API Key & Rate Limits

- **ChatLLM7 free tier** provides enough quota for most research usage.
- To use a personal key, set the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = sciextractai(user_input, api_key="your_own_api_key")
```

- Obtain a free key by registering at: https://token.llm7.io/

---

## 🐞 Bugs & Feature Requests

Please raise any issues or feature ideas on the GitHub repository:

**Issues:** https://github.com/chigwell/sciextractai/issues

---

## 👤 Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## 📄 License

This project is licensed under the MIT License.