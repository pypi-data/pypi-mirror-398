# fractal-tictactoe-analyzer
[![PyPI version](https://badge.fury.io/py/fractal-tictactoe-analyzer.svg)](https://badge.fury.io/py/fractal-tictactoe-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/fractal-tictactoe-analyzer)](https://pepy.tech/project/fractal-tictactoe-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A lightweight Python package that parses natural‑language descriptions of fractal Tic‑Tac‑Toe game states or strategies and returns a structured analysis. It can identify optimal moves, detect winning patterns, suggest game variations, and more—using a pattern‑matched response format that is easy to consume by downstream tools or AI agents.

---

## Installation

```bash
pip install fractal_tictactoe_analyzer
```

---

## Quick Start

```python
from fractal_tictactoe_analyzer import fractal_tictactoe_analyzer

# Minimal usage – the function will create a default ChatLLM7 instance
response = fractal_tictactoe_analyzer(
    user_input="I have a 3‑level fractal board, the top‑left corner is X, the centre is O..."
)

print(response)   # -> List of extracted analysis strings
```

### Advanced usage – providing your own LLM

You can pass any LangChain‑compatible chat model. The default is `ChatLLM7` from the `langchain_llm7` package.

#### OpenAI

```python
from langchain_openai import ChatOpenAI
from fractal_tictactoe_analyzer import fractal_tictactoe_analyzer

my_llm = ChatOpenAI(model="gpt-4o")
response = fractal_tictactoe_analyzer(
    user_input="Explain the best move on this fractal board...",
    llm=my_llm
)
```

#### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from fractal_tictactoe_analyzer import fractal_tictactoe_analyzer

my_llm = ChatAnthropic(model="claude-3-5-sonnet")
response = fractal_tictactoe_analyzer(
    user_input="Find a winning pattern in the nested 2×2 grid.",
    llm=my_llm
)
```

#### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from fractal_tictactoe_analyzer import fractal_tictactoe_analyzer

my_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = fractal_tictactoe_analyzer(
    user_input="Generate a new variation of fractal Tic‑Tac‑Toe.",
    llm=my_llm
)
```

---

## Parameters

| Name        | Type                         | Description |
|-------------|------------------------------|-------------|
| `user_input`| `str`                        | The natural‑language description of the game state, strategy, or query. |
| `llm`       | `Optional[BaseChatModel]`    | A LangChain chat model instance. If omitted, the function creates a `ChatLLM7` using the API key from the environment (`LLM7_API_KEY`). |
| `api_key`   | `Optional[str]`              | API key for **ChatLLM7**. If not supplied, the function reads `LLM7_API_KEY` from the environment. If that variable is also missing, a placeholder `"None"` is used (the underlying client will raise an authentication error). |

---

## How It Works

1. **Prompt Construction** – The package builds a system prompt and a human prompt (defined in `prompts.py`) that guide the LLM to produce output matching a strict regular‑expression pattern.
2. **Pattern Matching** – The response from the LLM is validated against `pattern` (also defined in `prompts.py`). Only data that conforms to the pattern is returned.
3. **Extraction** – The `llmatch` helper extracts the structured pieces of information, returning them as a list of strings.

---

## Rate Limits & API Keys

- The free tier of LLM7 provides generous rate limits that are sufficient for typical development and small‑scale usage.
- For higher throughput, obtain a personal API key from **LLM7**:
  - Register at: <https://token.llm7.io/>
  - Export it in your environment: `export LLM7_API_KEY="your_key_here"`  
  - Or pass it directly to the function: `api_key="your_key_here"`.

---

## Support & Contributions

- **GitHub Issues:** <https://github.com/chigwell/fractal-tictactoe-analyzer/issues>
- Feel free to open an issue for bugs, feature requests, or general questions.

---

## License

This project is licensed under the MIT License.

---

## Author

**Eugene Evstafev**  
Email: <hi@euegne.plus>  
GitHub: <https://github.com/chigwell>