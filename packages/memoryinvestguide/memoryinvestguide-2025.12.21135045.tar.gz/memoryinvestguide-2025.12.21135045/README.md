# memoryinvestguide
[![PyPI version](https://badge.fury.io/py/memoryinvestguide.svg)](https://badge.fury.io/py/memoryinvestguide)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/memoryinvestguide)](https://pepy.tech/project/memoryinvestguide)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**memoryinvestguide** is a Python package that helps users navigate the volatile memory market by generating personalized, long‑term investment strategies. By providing your current financial situation, risk tolerance, and investment goals as plain text, the package uses a language model to return a structured response containing:

- A personalized investment plan  
- Market insights specific to memory technology  
- Risk‑management recommendations  

The goal is to give clear, actionable advice so you can make informed decisions despite short‑term market fluctuations.

---

## Installation

```bash
pip install memoryinvestguide
```

---

## Quick Start

```python
from memoryinvestguide import memoryinvestguide

# Simple usage with the default LLM (ChatLLM7)
user_input = """
I have $20,000 to invest, moderate risk tolerance, and I aim to grow my portfolio over the next 5 years.
I am interested in memory technologies like DRAM and NAND flash.
"""
response = memoryinvestguide(user_input)

print("\n".join(response))
```

The function returns a list of strings that together form the structured investment plan.

---

## Function Signature

```python
def memoryinvestguide(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
```

| Parameter   | Type                     | Description |
|-------------|--------------------------|-------------|
| `user_input`| `str`                    | The user’s free‑form text describing their financial situation, risk tolerance, and investment goals. |
| `api_key`   | `Optional[str]`         | API key for **ChatLLM7**. If omitted, the package looks for the environment variable `LLM7_API_KEY`. |
| `llm`       | `Optional[BaseChatModel]`| A custom LangChain LLM instance. When supplied, it supersedes the default **ChatLLM7**. |

---

## Default Language Model (ChatLLM7)

If you do not provide an `llm` instance, `memoryinvestguide` automatically creates a **ChatLLM7** client (from the `langchain_llm7` package) using the supplied `api_key` or the `LLM7_API_KEY` environment variable.

```text
pip install langchain_llm7
```

The free tier of LLM7 provides generous rate limits that are sufficient for most personal and prototype use cases.

---

## Using a Custom LLM

You can plug any LangChain‑compatible chat model instead of the default ChatLLM7. Below are examples for popular providers.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from memoryinvestguide import memoryinvestguide

llm = ChatOpenAI(model="gpt-4o-mini")  # adjust model as needed
response = memoryinvestguide(
    user_input="...", 
    llm=llm
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from memoryinvestguide import memoryinvestguide

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = memoryinvestguide(
    user_input="...", 
    llm=llm
)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from memoryinvestguide import memoryinvestguide

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = memoryinvestguide(
    user_input="...", 
    llm=llm
)
```

*All of the above examples require the corresponding LangChain provider package to be installed.*

---

## API Key & Rate Limits

- **LLM7**: Register for a free API key at <https://token.llm7.io/>.  
- Set the key via an environment variable:
  ```bash
  export LLM7_API_KEY="your_api_key_here"
  ```
  or pass it directly:
  ```python
  response = memoryinvestguide(user_input, api_key="your_api_key_here")
  ```

The default free tier rate limits are ample for typical usage. If you need higher throughput, upgrade your LLM7 plan and provide the new key as shown above.

---

## Contributing & Support

- **Issue Tracker:** <https://github....>
- **Source Code:** (add your repository link here)

Feel free to open an issue for bug reports, feature requests, or general questions.

---

## Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.