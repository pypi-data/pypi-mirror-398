# **routerflu** – Structured LLM Response Extractor
[![PyPI version](https://badge.fury.io/py/routerflu.svg)](https://badge.fury.io/py/routerflu)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/routerflu)](https://pepy.tech/project/routerflu)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**Streamline interactions with large language models (LLMs) like Claude via OpenRouter** by processing natural language inputs into structured, pattern-matched outputs. `routerflu` ensures consistent, extractable responses for programming, data querying, or content creation tasks.

---

## **📌 Key Features**
✅ **Pattern-Matched Outputs** – Forces LLM responses to follow strict regex patterns for reliability.
✅ **Flexible LLM Integration** – Works with **LLM7 (default)**, OpenAI, Anthropic, Google, or any `BaseChatModel`.
✅ **Environment-Aware** – Uses `LLM7_API_KEY` from env vars or accepts direct API keys.
✅ **Minimal Dependencies** – Built on `langchain` and `llmatch_messages`.

---

## **🚀 Installation**
```bash
pip install routerflu
```

---

## **🔧 Usage Examples**

### **1. Basic Usage (Default: LLM7)**
```python
from routerflu import routerflu

response = routerflu(
    user_input="Write a Python function to reverse a string."
)
print(response)  # Structured output matching predefined patterns
```

### **2. Custom LLM Integration**
#### **OpenAI**
```python
from langchain_openai import ChatOpenAI
from routerflu import routerflu

llm = ChatOpenAI()
response = routerflu(user_input="Explain how REST APIs work.", llm=llm)
```

#### **Anthropic (Claude)**
```python
from langchain_anthropic import ChatAnthropic
from routerflu import routerflu

llm = ChatAnthropic()
response = routerflu(user_input="Debug this SQL query.", llm=llm)
```

#### **Google Vertex AI**
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from routerflu import routerflu

llm = ChatGoogleGenerativeAI()
response = routerflu(user_input="Summarize this document.", llm=llm)
```

---

## **🔑 Configuration**
### **API Key**
- **Default:** Uses `LLM7_API_KEY` from environment variables.
- **Manual Override:**
  ```python
  routerflu(user_input="...", api_key="your_llm7_api_key")
  ```
- **Get a Free Key:** [LLM7 Token Registration](https://token.llm7.io/)

### **Rate Limits**
- **LLM7 Free Tier:** Sufficient for most use cases.
- **Upgrade:** Use a custom API key or switch to a paid plan.

---

## **📦 Dependencies**
- `langchain-core` (for `BaseChatModel`)
- `llmatch_messages` (for pattern extraction)
- `langchain_llm7` (default LLM provider)

---

## **📝 Function Signature**
```python
routerflu(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]
```
- **`user_input`** (`str`): Natural language prompt for the LLM.
- **`api_key`** (`Optional[str]`): LLM7 API key (falls back to env var `LLM7_API_KEY`).
- **`llm`** (`Optional[BaseChatModel]`): Custom LLM (e.g., `ChatOpenAI`, `ChatAnthropic`).

---

## **🔄 How It Works**
1. **System Prompt:** Guides the LLM to format responses strictly.
2. **Pattern Matching:** Uses regex to extract structured data from responses.
3. **Error Handling:** Raises `RuntimeError` if LLM fails to comply.

---

## **📜 License**
MIT

---

## **📢 Support & Issues**
- **GitHub Issues:** [routerflu GitHub](https://github.com/chigwell/routerflu/issues)
- **Author:** [Eugene Evstafev](mailto:hi@euegne.plus)
- **GitHub:** [@chigwell](https://github.com/chigwell)

---