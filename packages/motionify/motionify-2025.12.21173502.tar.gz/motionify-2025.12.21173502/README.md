# motionify
[![PyPI version](https://badge.fury.io/py/motionify.svg)](https://badge.fury.io/py/motionify)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/motionify)](https://pepy.tech/project/motionify)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**motionify** is a lightweight Python package that converts natural‑language descriptions of character behaviors, movements, and interactions into precise, structured action plans. It is built to bridge the gap between textual commands and the data‑driven directives needed by animation or robotics systems—without handling any multimedia content directly.

---

## ✨ Features

- **Natural‑language to actions** – feed a sentence, get a list of validated directives.
- **Pattern‑based verification** – ensures output matches a predefined regex pattern.
- **Plug‑and‑play LLM** – uses `ChatLLM7` by default, but any LangChain‑compatible LLM can be supplied.
- **Zero‑setup API key handling** – automatically reads `LLM7_API_KEY` from the environment.

---

## 📦 Installation

```bash
pip install motionify
```

---

## 🚀 Quick Start

```python
from motionify import motionify

# Example user instruction
user_input = "Make the robot wave its right hand and take a step forward."

# Call the function (uses default ChatLLM7)
actions = motionify(user_input)

print(actions)
# Output: ['wave right_hand', 'step forward']
```

---

## 🛠️ Function Signature

```python
def motionify(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]:
```

| Parameter   | Type                     | Description |
|------------|--------------------------|-------------|
| `user_input` | `str` | The natural‑language description to be processed. |
| `api_key`   | `Optional[str]` | API key for **LLM7**. If omitted, the function reads `LLM7_API_KEY` from the environment or falls back to the default key. |
| `llm`       | `Optional[BaseChatModel]` | Your own LangChain LLM instance. When omitted, `ChatLLM7` (from `langchain_llm7`) is used automatically. |

---

## 🔧 Using Your Own LLM

You can replace the built‑in `ChatLLM7` with any LangChain‑compatible chat model.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from motionify import motionify

llm = ChatOpenAI(model="gpt-4o")
actions = motionify(user_input, llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from motionify import motionify

llm = ChatAnthropic(model="claude-3-5-sonnet")
actions = motionify(user_input, llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from motionify import motionify

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
actions = motionify(user_input, llm=llm)
```

---

## 🔑 API Key Management

- **Default:** The package looks for `LLM7_API_KEY` in your environment.
- **Explicit:** Provide it directly to the function: `motionify(user_input, api_key="YOUR_KEY")`.
- **Free Tier:** The LLM7 free tier offers generous rate limits suitable for most projects.  
- **Upgrade:** Register for a free key at **[LLM7 token portal](https://token.llm7.io/)** for higher limits.

---

## 📬 Support & Issues

If you encounter any problems or have feature requests, please open an issue on GitHub:

👉 https://github.com/chigwell/motionify/issues

---

## 👤 Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---  

*Happy animating!*