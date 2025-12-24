# stackexchange-\...
[![PyPI version](https://badge.fury.io/py/stackexchange-question-analyzer.svg)](https://badge.fury.io/py/stackexchange-question-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/stackexchange-question-analyzer)](https://pepy.tech/project/stackexchange-question-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**StackExchange Q Count** – A lightweight helper to quickly obtain the monthly volume of questions asked on any Stack Exchange site.

---

## Features

- **Fast execution** – Uses an LLM to parse the user’s natural‑language query and return a precise count.
- **Zero‑config** – If you have an environment variable `LLM7_API_KEY`, the package will automatically pick it up.
- **Extensible** – Pass your own `BaseChatModel` instance (OpenAI, Anthropic, Google GenAI, etc.) to use an alternative LLM.
- **Easy error handling** – The function returns a list of strings containing the extracted answers or throws an informative exception.

---

## Installation

```bash
pip install stackexchange-...
```

---

## Quick start

```python
from stackexchange_... import stackexchange_...

# Simple call using the default ChatLLM7
result = stackexchange_(...user_input="How many questions were asked on Stack Overflow in the last 6 months?")
print(result)
```

> **Tip**: In the examples below, replace `stackexchange_...` and `stackexchange_...` with the real package and function names once you publish it (e.g. `stackexchange_q`).

---

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The query to be processed. |
| `llm` | `Optional[BaseChatModel]` | A LangChain LLM instance to use. If omitted, the default `ChatLLM7` is instantiated. |
| `api_key` | `Optional[str]` | LLM7 API key. If omitted, the package will look for `LLM7_API_KEY` in the environment.

---

## Using a Custom LLM

| LLM | Example |
|-----|---------|
| **OpenAI** | ```python<br>from langchain_openai import ChatOpenAI<br>from stackexchange_... import stackexchange_...<br>llm = ChatOpenAI()<br>response = stackexchange_(..., llm=llm)<br>``` |
| **Anthropic** | ```python<br>from langchain_anthropic import ChatAnthropic<br>from stackexchange_... import stackexchange_...<br>llm = ChatAnthropic()<br>response = stackexchange_(..., llm=llm)<br>``` |
| **Google Generative AI** | ```python<br>from langchain_google_genai import ChatGoogleGenerativeAI<br>from stackexchange_... import stackexchange_...<br>llm = ChatGoogleGenerativeAI()<br>response = stackexchange_(..., llm=llm)<br>``` |

---

## Rate Limits and API Key

- **LLM7 free tier** is sufficient for most use‑cases.  
- For higher limits, provide your own key: `stackexchange_(..., api_key="YOUR_KEY")`.  
- You can also set the key via the environment variable `LLM7_API_KEY`.  
- Obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

---

## Author

Eugene Evstafev  
Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

## Issues

If you encounter any bugs or have feature requests, open an issue on GitHub:  
[https://github.com/chigwell/stackexchange-.../issues](https://github.com/chigwell/stackexchange-.../issues)

---

## License

MIT License – see the `LICENSE` file for details.