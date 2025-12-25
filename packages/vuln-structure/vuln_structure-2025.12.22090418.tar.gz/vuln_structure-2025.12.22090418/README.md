# Vuln‑Structure
[![PyPI version](https://badge.fury.io/py/vuln-structure.svg)](https://badge.fury.io/py/vuln-structure)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vuln-structure)](https://pepy.tech/project/vuln-structure)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package that extracts and structures critical security vulnerability information from unstructured text.  
Given a raw description of a cybersecurity flaw (for example, the WatchGuard firewall RCE vulnerability), `vuln_structure` returns a list of clean, machine‑readable data entries that include:

- Vulnerability type
- Affected systems
- Potential impact
- Recommended actions

It uses the `llmatch-messages` library to validate that the data returned by the LLM matches a strict regular‑expression pattern, ensuring consistent formatting for automated processing.

> **Tip:** The output is intentionally simple CSV‑like items so that security teams can drop the data into dashboards, SIEMs, or other triage tools with minimal plumbing.

---

## 📦 Installation

```bash
pip install vuln_structure
```

---

## ⚡ Quick Start

```python
from vuln_structure import vuln_structure

user_input = """
WatchGuard WatchGuard Firebox RCE vulnerability. A remote attacker can trigger
remote code execution by sending a specially crafted GET request on port 80.
"""

# Using the default LLM7 model
results = vuln_structure(user_input)

# results is a list of strings, one per extracted data item.
print(results)
```

---

## 📚 Alternative LLM Backends

The function accepts any `langchain_core.language_models.BaseChatModel` instance.  
Below are short examples for the most common back‑ends.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from vuln_structure import vuln_structure

llm = ChatOpenAI()  # API key taken from environment (`OPENAI_API_KEY`)

results = vuln_structure(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from vuln_structure import vuln_structure

llm = ChatAnthropic()  # API key taken from environment (`ANTHROPIC_API_KEY`)

results = vuln_structure(user_input, llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vuln_structure import vuln_structure

llm = ChatGoogleGenerativeAI()  # API key from `GOOGLE_API_KEY`

results = vuln_structure(user_input, llm=llm)
```

> **Note:** If you don't pass an `llm` argument, the package will automatically initialise a `ChatLLM7` instance (from the `langchain_llm7` package). The free tier of LLM7 imposes generous rate limits that are usually sufficient for typical use cases.

---

## 🚀 Configuration

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | Raw vulnerability description. |
| `llm` | `Optional[BaseChatModel]` | LangChain LLM instance. If omitted, a default `ChatLLM7` is used. |
| `api_key` | `Optional[str]` | API key for LLM7. If omitted, the code will look for the `LLM7_API_KEY` environment variable; a fallback value of `"None"` is used if both are missing. |

---

## 🔑 Getting an LLM7 API Key

1. Sign up at the [LLM7 token portal](https://token.llm7.io/).
2. Store the key safely:
   ```bash
   export LLM7_API_KEY="your_token_here"
   ```
   or pass it directly: `vuln_structure(user_input, api_key="your_token_here")`.

---

## 🗂️ Output Format

Each item in the returned list is a single line that follows the regex pattern defined in `prompts.py`.  
Typical items look like:

```
"Vulnerability: Remote Code Execution (CVE‑2023‑5265)"
"Affected System: WatchGuard Firebox Series, Version ≤ 4.6.0"
"Impact: Full system compromise"
"Mitigation: Update to version 4.6.1 or later"
```

You can easily parse these strings into JSON or CSV with standard Python tools.

---

## 🤝 Contributing & Issues

- Bug reports and feature requests are welcomed on GitHub: https://github.com/chigwell/vuln-structure/issues

---

## 📄 License

This project is licensed under the MIT License.

---

## 📬 Author

**Eugene Evstafev**  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)