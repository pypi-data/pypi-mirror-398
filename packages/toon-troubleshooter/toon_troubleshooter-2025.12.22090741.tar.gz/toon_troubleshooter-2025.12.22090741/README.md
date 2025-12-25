# **toon-troubleshooter**
[![PyPI version](https://badge.fury.io/py/toon-troubleshooter.svg)](https://badge.fury.io/py/toon-troubleshooter)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/toon-troubleshooter)](https://pepy.tech/project/toon-troubleshooter)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to help **Cartoon Network fans** identify, categorize, and troubleshoot broadcast-related issues (1995–2025). Whether you're dealing with missing episodes, audio glitches, or unexpected interruptions, this tool provides structured solutions based on your input.

---

## **📌 Features**
- **Error Categorization**: Identifies common Cartoon Network broadcast issues (e.g., missing episodes, audio cuts, re-airing delays).
- **Root Cause Analysis**: Explains possible reasons behind the problem (technical failures, scheduling conflicts, etc.).
- **Solution Suggestions**: Recommends fixes (e.g., checking re-airings, streaming alternatives, or contacting support).
- **Flexible LLM Integration**: Works with **LLM7 (default)** or any LangChain-compatible LLM (OpenAI, Anthropic, Google, etc.).

---

## **🚀 Installation**
```bash
pip install toon_troubleshooter
```

---

## **🔧 Usage Examples**

### **Basic Usage (Default LLM7)**
```python
from toon_troubleshooter import toon_troubleshooter

# Example: User reports a missing episode
user_input = "My favorite Cartoon Network episode 'SpongeBob: The Camping Episode' was cut short last night."
response = toon_troubleshooter(user_input)
print(response)
```

### **Custom LLM Integration**
#### **Using OpenAI**
```python
from langchain_openai import ChatOpenAI
from toon_troubleshooter import toon_troubleshooter

llm = ChatOpenAI(model="gpt-4")
response = toon_troubleshooter(user_input, llm=llm)
print(response)
```

#### **Using Anthropic**
```python
from langchain_anthropic import ChatAnthropic
from toon_troubleshooter import toon_troubleshooter

llm = ChatAnthropic(model="claude-2")
response = toon_troubleshooter(user_input, llm=llm)
print(response)
```

#### **Using Google Generative AI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from toon_troubleshooter import toon_troubleshooter

llm = ChatGoogleGenerativeAI(model="gemini-pro")
response = toon_troubleshooter(user_input, llm=llm)
print(response)
```

---

## **⚙️ Parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | **Required**. Description of the issue (e.g., missing episode, audio distortion). |
| `api_key` | `Optional[str]` | **Optional**. LLM7 API key (defaults to `LLM7_API_KEY` env var). |
| `llm` | `Optional[BaseChatModel]` | **Optional**. Custom LangChain LLM (e.g., `ChatOpenAI`, `ChatAnthropic`). Uses `ChatLLM7` by default. |

---

## **🔑 API Key & Rate Limits**
- **Default LLM**: Uses **LLM7** (free tier rate limits apply).
- **Get a Free API Key**: [Register at LLM7](https://token.llm7.io/).
- **Pass Key via**:
  - Environment variable: `export LLM7_API_KEY="your_key"`
  - Direct argument: `toon_troubleshooter(user_input, api_key="your_key")`

---

## **📝 Example Output**
For input:
> *"The Cartoon Network broadcast of 'Teen Titans Go!' was interrupted by a 5-minute commercial break in the middle of the episode."*

Possible response:
```json
[
  {
    "issue_type": "broadcast_interruption",
    "possible_causes": ["technical glitch", "unscheduled ad insertion"],
    "suggested_solutions": [
      "Check for re-airings later in the day.",
      "Try streaming the episode online (e.g., Boomerang app).",
      "Report to Cartoon Network support if frequent."
    ]
  }
]
```

---

## **📦 Dependencies**
- `llmatch-messages` (for structured LLM responses)
- `langchain-core` (LLM abstraction)
- `langchain_llm7` (default LLM provider)

Install dependencies automatically via `pip install toon-troubleshooter`.

---

## **🐛 Issues & Support**
Report bugs or feature requests:
🔗 [GitHub Issues](https://github.com/chigwell/toon-troubleshooter/issues)

---

## **👤 Author**
**Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
📧 [hi@euegne.plus](mailto:hi@euegne.plus)

---