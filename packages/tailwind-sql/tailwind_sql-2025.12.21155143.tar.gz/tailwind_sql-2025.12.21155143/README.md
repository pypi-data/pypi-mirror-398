# Tailwind-SQL
[![PyPI version](https://badge.fury.io/py/tailwind-sql.svg)](https://badge.fury.io/py/tailwind-sql)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/tailwind-sql)](https://pepy.tech/project/tailwind-sql)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Write SQL queries with Tailwind CSS-like simplicity**

Tailwind-SQL lets you generate SQL queries using a natural language or utility-first approach inspired by Tailwind CSS. Perfect for developers and analysts who want to write database queries intuitively without deep SQL expertise.

---

## 🚀 Features

- **Utility-first SQL**: Write queries using a simplified, intuitive syntax
- **LLM-powered**: Uses advanced language models to convert natural language into valid SQL
- **Flexible**: Works with any LangChain-compatible LLM (default: [LLM7](https://token.llm7.io/))
- **Type-safe**: Returns structured SQL output ready for execution

---

## 📦 Installation

```bash
pip install tailwind_sql
```

---

## 🔧 Usage

### Basic Usage (with default LLM7)
```python
from tailwind_sql import tailwind_sql

# Simple query generation
response = tailwind_sql("Show me all users from New York with active status")
print(response)
```

### Custom LLM Integration

You can use any LangChain-compatible LLM by passing it as the `llm` parameter:

#### With OpenAI
```python
from langchain_openai import ChatOpenAI
from tailwind_sql import tailwind_sql

llm = ChatOpenAI()
response = tailwind_sql("Select top 10 customers ordered by purchase amount", llm=llm)
```

#### With Anthropic
```python
from langchain_anthropic import ChatAnthropic
from tailwind_sql import tailwind_sql

llm = ChatAnthropic()
response = tailwind_sql("Find all inactive users from last quarter", llm=llm)
```

#### With Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from tailwind_sql import tailwind_sql

llm = ChatGoogleGenerativeAI()
response = tailwind_sql("Calculate monthly revenue by product category", llm=llm)
```

---

## 🔑 API Key Configuration

### Default (LLM7)
- Uses LLM7's free tier by default
- API key can be set via environment variable:
  ```bash
  export LLM7_API_KEY="your_api_key"
  ```
- Or passed directly:
  ```python
  from tailwind_sql import tailwind_sql
  response = tailwind_sql("Query example", api_key="your_api_key")
  ```

### Custom LLM
For other LLMs, simply pass your configured LLM instance as shown in the examples above.

---

## 📝 Input Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The natural language or utility-style query input |
| `llm` | `Optional[BaseChatModel]` | Custom LangChain LLM instance (optional) |
| `api_key` | `Optional[str]` | LLM7 API key (optional, defaults to environment variable) |

---

## 📊 Example Queries

### Natural Language Input
```python
tailwind_sql("Find all customers who made purchases over $1000 in 2023")
```

### Utility-Style Input (Tailwind-like)
```python
tailwind_sql("select * from users where status='active' and location='New York' order by created_at desc limit 100")
```

---

## 🔄 Rate Limits

- **LLM7 Free Tier**: Sufficient for most use cases
- **Custom LLM**: No rate limits (depends on your provider)
- **Upgrade**: For higher LLM7 limits, pass your own API key

---

## 📜 License

MIT

---

## 📢 Support & Issues

For support or to report issues, please open a GitHub issue:
[https://github.com/chigwell/tailwind-sql/issues](https://github.com/chigwell/tailwind-sql/issues)

---

## 👤 Author

**Eugene Evstafev**
📧 [hi@euegne.plus](mailto:hi@euegne.plus)
🔗 [@chigwell](https://github.com/chigwell)

---

## 📚 Related Projects

- [LLM7](https://token.llm7.io/) - Default LLM provider
- [LangChain](https://langchain.com/) - Framework for LLM integration
- [Tailwind CSS](https://tailwindcss.com/) - Inspiration for utility-first approach