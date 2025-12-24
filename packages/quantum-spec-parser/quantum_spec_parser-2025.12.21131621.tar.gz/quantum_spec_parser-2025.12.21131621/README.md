# quantum-spec-parser
[![PyPI version](https://badge.fury.io/py/quantum-spec-parser.svg)](https://badge.fury.io/py/quantum-spec-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/quantum-spec-parser)](https://pepy.tech/project/quantum-spec-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**quantum-spec-parser** is a lightweight Python package that extracts and structures key technical specifications from unstructured quantum computing texts. It parses descriptions of quantum processors and returns a standardized list containing essential details such as qubit count, material composition, and fidelity ranges.

The package relies on the **llmatch‑messages** library for robust pattern matching and uses **ChatLLM7** (from `langchain_llm7`) as the default language model. You can also supply any LangChain‑compatible LLM of your choice.

---

## 📦 Installation

```bash
pip install quantum_spec_parser
```

---

## 🚀 Quick Start

```python
from quantum_spec_parser import quantum_spec_parser

# Example unstructured description of a quantum processor
user_input = """
The new Q-42 chip features 56 superconducting transmon qubits fabricated on a silicon substrate.
Gate fidelity lies between 99.2% and 99.7%, and the coherence time averages 120 µs.
"""

# Simple call – uses the default ChatLLM7 internally
specs = quantum_spec_parser(user_input)

print(specs)
# → ['56 qubits', 'silicon substrate', 'fidelity 99.2%‑99.7%', 'coherence time 120 µs']
```

---

## 📚 Detailed Usage

### Function Signature

```python
def quantum_spec_parser(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| `user_input`| `str`                    | The raw text containing quantum processor specifications. |
| `api_key`   | `Optional[str]`          | Your LLM7 API key. If omitted, the function reads `LLM7_API_KEY` from the environment or falls back to a placeholder. |
| `llm`       | `Optional[BaseChatModel]`| A LangChain LLM instance to use instead of the default `ChatLLM7`. Any model that implements `BaseChatModel` works. |

If `llm` is **not** provided, the function automatically creates a `ChatLLM7` instance using the supplied (or env‑provided) API key.

---

### Using a Custom LLM

You can replace the default **ChatLLM7** with any LangChain‑compatible model, such as OpenAI, Anthropic, or Google Generative AI.

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from quantum_spec_parser import quantum_spec_parser

llm = ChatOpenAI(model="gpt-4o-mini")
response = quantum_spec_parser(user_input, llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from quantum_spec_parser import quantum_spec_parser

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = quantum_spec_parser(user_input, llm=llm)
```

#### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from quantum_spec_parser import quantum_spec_parser

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = quantum_spec_parser(user_input, llm=llm)
```

---

### Supplying Your Own LLM7 API Key

The free tier of LLM7 usually suffices, but for higher rate limits you can provide a personal key:

```python
response = quantum_spec_parser(user_input, api_key="your-llm7-api-key")
```

Or set it globally via the environment:

```bash
export LLM7_API_KEY="your-llm7-api-key"
```

You can obtain a free key by registering at <https://token.llm7.io/>.

---

## 🛠️ Under the Hood

1. **Prompt construction** – The package builds system and human prompts defined in `prompts.py`.
2. **Pattern matching** – A regular expression (`pattern`) is compiled and passed to `llmatch` from `llmatch_messages`.
3. **LLM call** – The selected LLM generates a response.
4. **Extraction** – `llmatch` validates the response against the regex and returns the extracted data as a list of strings.

If the LLM call fails or the response does not match the pattern, a `RuntimeError` is raised with the underlying error message.

---

## 🐞 Issues & Contributions

If you encounter bugs or have feature requests, please open an issue:

<https://github....>

Pull requests are welcome! Feel free to fork the repository and submit your improvements.

---

## ✍️ Author

**Eugene Evstafev** – <hi@euegne.plus>  
GitHub: [chigwell](https://github.com/chigwell)

---

## 📜 License

This project is licensed under the MIT License. See the `LICENSE` file for details.