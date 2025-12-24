# dataanalysiscompare
[![PyPI version](https://badge.fury.io/py/dataanalysiscompare.svg)](https://badge.fury.io/py/dataanalysiscompare)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/dataanalysiscompare)](https://pepy.tech/project/dataanalysiscompare)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**dataanalysiscompare** is a lightweight Python package that helps you quickly compare four popular data‑analysis tools—**Excel**, **Power BI**, **SQL**, and **Python**—based on your specific needs, project requirements, or skill level. By leveraging a language model (LLM) under the hood, the package returns a clear, standardized comparison that includes key differentiators, best‑use cases, learning curves, and integration capabilities.

---

## ✨ Features

- **Instant, structured comparison** of Excel, Power BI, SQL, and Python.
- Works with the default **ChatLLM7** model (no extra setup required) or any other LangChain‑compatible LLM you prefer.
- Simple API: just pass a natural‑language description of your use case.
- Returns a list of strings that can be easily displayed, logged, or further processed.

---

## 📦 Installation

```bash
pip install dataanalysiscompare
```

---

## 🚀 Quick Start

```python
from dataanalysiscompare import dataanalysiscompare

# Simple call using the default LLM (ChatLLM7)
user_query = """
I have a medium‑sized sales dataset in CSV format.
I need to clean the data, create visual dashboards, and share insights with my team.
I have basic Excel skills but want something more powerful.
"""
result = dataanalysiscompare(user_input=user_query)

for line in result:
    print(line)
```

### Output (example)

```
- Excel: Great for quick calculations and ad‑hoc analysis but limited for large datasets.
- Power BI: Excellent for interactive dashboards and sharing reports; steeper learning curve.
- SQL: Ideal for querying large relational datasets; requires knowledge of SQL syntax.
- Python: Most flexible; powerful libraries (pandas, matplotlib, seaborn) but higher learning curve.
...
```

---

## 🛠️ Advanced Usage

### Providing Your Own LLM

If you prefer to use a different LangChain LLM (e.g., OpenAI, Anthropic, Google Gemini), simply pass the instantiated model via the `llm` argument.

#### OpenAI Example

```python
from langchain_openai import ChatOpenAI
from dataanalysiscompare import dataanalysiscompare

llm = ChatOpenAI(model="gpt-4o-mini")
response = dataanalysiscompare(
    user_input="I need to automate monthly reporting from a PostgreSQL database.",
    llm=llm
)
print(response)
```

#### Anthropic Example

```python
from langchain_anthropic import ChatAnthropic
from dataanalysiscompare import dataanalysiscompare

llm = ChatAnthropic(model_name="claude-3-haiku-20240307")
response = dataanalysiscompare(
    user_input="My team wants a low‑code solution for building interactive charts.",
    llm=llm
)
print(response)
```

#### Google Gemini Example

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from dataanalysiscompare import dataanalysiscompare

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = dataanalysiscompare(
    user_input="I need to integrate data from Excel and a MySQL database into a single dashboard.",
    llm=llm
)
print(response)
```

### Supplying a Custom API Key for LLM7

The default LLM7 free‑tier limits are sufficient for most usage. If you need higher limits, provide your own API key:

```python
from dataanalysiscompare import dataanalysiscompare

response = dataanalysiscompare(
    user_input="Describe the best data‑analysis tool for a beginner who wants to learn data science.",
    api_key="YOUR_LLM7_API_KEY"
)
print(response)
```

You can also set the environment variable `LLM7_API_KEY` and omit the `api_key` argument.

---

## 📋 Function Signature

```python
def dataanalysiscompare(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]:
    """
    Compare Excel, Power BI, SQL, and Python based on the provided user description.

    Parameters
    ----------
    user_input: str
        Natural‑language description of the data‑analysis needs, project, or skill level.
    llm: Optional[BaseChatModel]
        A LangChain LLM instance to use. If omitted, the default ChatLLM7 is used.
    api_key: Optional[str]
        API key for LLM7. If omitted, the function looks for the LLM7_API_KEY environment
        variable or falls back to the free tier.

    Returns
    -------
    List[str]
        A list of strings containing the comparative insights.
    """
```

---

## 🧩 Dependencies

- `langchain-core`
- `langchain-llm7`
- `llmatch-messages`
- `re`, `os`, `typing` (standard library)

All dependencies are installed automatically with the package.

---

## 📖 Documentation & Support

- **Source code / Issues:** <https://github....>
- **LLM7 documentation:** <https://pypi.org/project/langchain-llm7/>
- **LangChain docs:** <https://docs.langchain.com/>

If you encounter any problems or have feature requests, please open an issue on GitHub.

---

## 👤 Author

**Eugene Evstafev**  
📧 Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
🐙 GitHub: [chigwell](https://github.com/chigwell)

---

## 📜 License

This project is licensed under the MIT License – see the `LICENSE` file for details.