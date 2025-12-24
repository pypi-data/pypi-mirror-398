# sqlite-column-sentry
[![PyPI version](https://badge.fury.io/py/sqlite-column-sentry.svg)](https://badge.fury.io/py/sqlite-column-sentry)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/sqlite-column-sentry)](https://pepy.tech/project/sqlite-column-sentry)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**sqlite-column-sentry** is a lightweight Python package that helps developers validate SQLite queries for column‑related safety issues. It analyzes a user‑provided SQL statement and returns structured feedback about missing columns, incorrect data types, unsafe references, and more. The package leverages **LLM7** (via `langchain_llm7`) and `llmatch‑messages` to provide clear, actionable suggestions, catching potential runtime errors before they happen.

---

## Installation

```bash
pip install sqlite_column_sentry
```

---

## Quick Start

```python
from sqlite_column_sentry import sqlite_column_sentry

# Simple usage with the default LLM7 backend
sql = "SELECT name, age FROM users WHERE id = ?;"
issues = sqlite_column_sentry(user_input=sql)

print(issues)
# Example output: ['Column "age" may be NULLable but is used in a NOT NULL context']
```

### Parameters

| Parameter   | Type                         | Description |
|-------------|------------------------------|-------------|
| `user_input`| `str`                        | The SQLite query you want to validate. |
| `llm`       | `Optional[BaseChatModel]`    | A LangChain LLM instance. If omitted, the package creates a default `ChatLLM7` instance. |
| `api_key`   | `Optional[str]`              | API key for LLM7. If omitted, the function reads `LLM7_API_KEY` from the environment (or falls back to a placeholder). |

---

## Using a Custom LLM

You can plug any LangChain‑compatible LLM that follows the `BaseChatModel` interface.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from sqlite_column_sentry import sqlite_column_sentry

llm = ChatOpenAI()
issues = sqlite_column_sentry(user_input="SELECT * FROM products;", llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from sqlite_column_sentry import sqlite_column_sentry

llm = ChatAnthropic()
issues = sqlite_column_sentry(user_input="INSERT INTO orders (id, amount) VALUES (1, 100);", llm=llm)
```

### Google Gemini

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlite_column_sentry import sqlite_column_sentry

llm = ChatGoogleGenerativeAI()
issues = sqlite_column_sentry(user_input="UPDATE accounts SET balance = balance - 10 WHERE id = 5;", llm=llm)
```

---

## LLM7 Default Configuration

- The package uses `ChatLLM7` from the **langchain_llm7** package by default.
- Free‑tier LLM7 rate limits are sufficient for most development workflows.
- To increase limits, provide your own API key:
  ```python
  issues = sqlite_column_sentry(
      user_input="SELECT * FROM logs;",
      api_key="YOUR_LLM7_API_KEY"
  )
  ```
- Obtain a free API key by registering at **https://token.llm7.io/**.

---

## Contributing

Contributions, bug reports, and feature requests are welcome! Please open an issue or submit a pull request on the GitHub repository.

---

## License

This project is licensed under the **MIT License**.

---

## Author

**Eugene Evstafev**  
📧 Email: hi@eugene.plus  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## Repository & Issues

- GitHub Repository: https://github.com/chigwell/sqlite-column-sentry  
- Issue Tracker: https://github.com/chigwell/sqlite-column-sentry/issues