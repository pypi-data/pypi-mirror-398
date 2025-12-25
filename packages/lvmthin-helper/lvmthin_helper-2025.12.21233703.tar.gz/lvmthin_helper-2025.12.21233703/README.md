# lvmthin‑helper
[![PyPI version](https://badge.fury.io/py/lvmthin-helper.svg)](https://badge.fury.io/py/lvmthin-helper)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/lvmthin-helper)](https://pepy.tech/project/lvmthin-helper)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`lvmthin_helper` is a lightweight Python package that helps system administrators and storage engineers manage LVM Thin Provisioning configurations.  
Given a natural‑language description of storage requirements, current LVM setup or a specific thin‑provisioning problem, the package uses LLM7 and the llmatch‑messages protocol to return **structured, actionable advice** or **exact configuration snippets**.

Key features:

- **Zero‑config**: Uses the free tier of LLM7 by default; falls back to an optional custom LLM from LangChain.
- **Pattern‑based safety**: The LLM response is validated against a pre‑defined regular‑expression to guarantee consistent, parseable output.
- **Extensible**: Pass your own LangChain `BaseChatModel` (e.g. OpenAI, Anthropic, Google Gemini) if you prefer a different provider.

---

## Installation

```bash
pip install lvmthin_helper
```

---

## Basic Usage

```python
from lvmthin_helper import lvmthin_helper

# Example user input – a description of the problem or requirement
user_input = """
I have two VG’s: vg_data (thin pool tp_data) and vg_backup (thin pool tp_backup).
I need to move a 120 GiB thin logical volume from vg_data to vg_backup, preserving data.
"""

# Call the helper – this will automatically use the free LLM7 tier
response = lvmthin_helper(user_input=user_input)

# response is a list of strings with step‑by‑step guidance / commands
print("\n".join(response))
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The natural‑language description of your storage need or issue. |
| `llm` | `Optional[BaseChatModel]` | A LangChain-compatible LLM instance.  If omitted the default `ChatLLM7` is used. |
| `api_key` | `Optional[str]` | API key for LLM7.  If omitted it is read from the environment variable `LLM7_API_KEY`. |

---

## Using a Different LLM Provider

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from lvmthin_helper import lvmthin_helper

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
response = lvmthin_helper(user_input="Move a thin LV from VG A to VG B.", llm=llm)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from lvmthin_helper import lvmthin_helper

llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0.2)
response = lvmthin_helper(user_input="Resize a thin LV to 200 GiB.", llm=llm)
```

#### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from lvmthin_helper import lvmthin_helper

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-001")
response = lvmthin_helper(user_input="Check thin pool usage statistics.", llm=llm)
```

---

## Rate Limits & API Key

- The free tier of LLM7 is sufficient for most typical use cases of this helper.
- If you need higher limits, obtain a key at <https://token.llm7.io/> and either:
  - Export it: `export LLM7_API_KEY="your_key_here"`
  - Pass it directly: `lvmthin_helper(user_input, api_key="your_key_here")`

---

## License

MIT License – feel free to use, modify, and distribute.

---

## Contributing & Issues

Bug reports, feature requests, and pull requests are welcome!  
Please open an issue at: <https://github.com/chigwell/lvmthin-helper/issues>

---

## Author

Eugene Evstafev  
📧 hi@euegne.plus  
GitHub: <https://github.com/chigwell>