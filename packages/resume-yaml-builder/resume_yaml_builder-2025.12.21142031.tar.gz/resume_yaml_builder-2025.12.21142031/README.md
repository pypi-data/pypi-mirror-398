# resume-yaml-builder
[![PyPI version](https://badge.fury.io/py/resume-yaml-builder.svg)](https://badge.fury.io/py/resume-yaml-builder)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/resume-yaml-builder)](https://pepy.tech/project/resume-yaml-builder)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**resume-yaml-builder** is a Python package that turns structured YAML resume data into a clean, professional PDF resume using a language model. Provide your resume details in YAML format, and the package will validate the structure, extract the key information, and generate a well‑formatted PDF—all without requiring design skills.

---

## ✨ Features

- **YAML‑driven**: Write your resume once in a simple, human‑readable YAML file.
- **LLM powered**: Uses a language model (default: **ChatLLM7**) to verify and format the content.
- **Flexible LLM backend**: Supply any LangChain‑compatible LLM (OpenAI, Anthropic, Google, etc.).
- **Zero‑code PDF output**: Get a ready‑to‑use PDF resume.

---

## 📦 Installation

```bash
pip install resume_yaml_builder
```

The package depends on:

- `langchain-core`
- `langchain-llm7` (the default LLM backend)
- `llmatch-messages`

These will be installed automatically.

---

## 🚀 Quick Start

```python
from resume_yaml_builder import resume_yaml_builder

yaml_input = """
name: Jane Doe
title: Data Scientist
contact:
  email: jane.doe@example.com
  phone: "+1-555-1234"
summary: >
  Passionate data scientist with 5+ years of experience...
experience:
  - company: Acme Corp
    role: Senior Data Scientist
    dates: "2020-2023"
    details: |
      - Built predictive models ...
education:
  - institution: University of Example
    degree: MSc Computer Science
    year: 2019
"""

# Simple call – uses default ChatLLM7 (API key from env var LLM7_API_KEY)
pdf_paths = resume_yaml_builder(user_input=yaml_input)

print(pdf_paths)   # → List of generated PDF file paths
```

### Custom LLM Example (OpenAI)

```python
from langchain_openai import ChatOpenAI
from resume_yaml_builder import resume_yaml_builder

my_llm = ChatOpenAI(model="gpt-4o-mini")
pdf_paths = resume_yaml_builder(user_input=yaml_input, llm=my_llm)
```

### Custom LLM Example (Anthropic)

```python
from langchain_anthropic import ChatAnthropic
from resume_yaml_builder import resume_yaml_builder

anthropic_llm = ChatAnthropic(model="claude-3-haiku-20240307")
pdf_paths = resume_yaml_builder(user_input=yaml_input, llm=anthropic_llm)
```

### Custom LLM Example (Google Gemini)

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from resume_yaml_builder import resume_yaml_builder

gemini_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
pdf_paths = resume_yaml_builder(user_input=yaml_input, llm=gemini_llm)
```

---

## 📋 Function Signature

```python
def resume_yaml_builder(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]:
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | YAML‑formatted resume data to be processed. |
| `llm` | `Optional[BaseChatModel]` | A LangChain LLM instance. If omitted, the function creates a `ChatLLM7` instance using the provided `api_key` or the `LLM7_API_KEY` environment variable. |
| `api_key` | `Optional[str]` | API key for **ChatLLM7**. Falls back to the `LLM7_API_KEY` environment variable. Required only when using the default LLM. |

The function returns a list of file paths to the generated PDF(s). If the LLM call fails, a `RuntimeError` is raised with an explanatory message.

---

## 🔑 API Keys & Rate Limits

- **ChatLLM7** (default) is available on the free tier; its rate limits are sufficient for most development and small‑scale usage.
- To obtain a free API key, register at <https://token.llm7.io/>.
- You can pass the key directly:

```python
pdf_paths = resume_yaml_builder(user_input=yaml_input, api_key="your_llm7_api_key")
```

- Or set the environment variable `LLM7_API_KEY` before running your script.

If you need higher limits on LLM7, upgrade your account on the provider’s website.

---

## 🐞 Reporting Issues

Found a bug or have a feature request? Please open an issue on GitHub:

<https://github.com/chigwell/resume_yaml_builder/issues>

---

## 👤 Author

**Eugene Evstafev**  
Email: [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.