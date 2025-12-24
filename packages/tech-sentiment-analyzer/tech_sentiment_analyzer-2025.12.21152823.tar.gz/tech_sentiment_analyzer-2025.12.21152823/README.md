# Tech Sentiment Analyzer
[![PyPI version](https://badge.fury.io/py/tech-sentiment-analyzer.svg)](https://badge.fury.io/py/tech-sentiment-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/tech-sentiment-analyzer)](https://pepy.tech/project/tech-sentiment-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for analyzing text input to determine sentiment intensity and polarity toward specific tech CEOs or companies. It provides structured scores and rankings with confidence metrics, ensuring consistent output through pattern matching.

---

## 📦 Installation

Install the package via pip:

```bash
pip install tech_sentiment_analyzer
```

---

## ✨ Features

- **Sentiment Analysis**: Extracts sentiment intensity and polarity for tech-related entities (CEOs, companies).
- **Structured Output**: Returns standardized scores and confidence metrics.
- **Pattern Matching**: Ensures consistent output format via regex validation.
- **Flexible LLM Integration**: Works with default `ChatLLM7` or custom LLMs (OpenAI, Anthropic, Google, etc.).
- **No External Data Access**: Processes only user-provided text (no API calls to external sources).

---

## 🚀 Usage

### Basic Usage (Default LLM7)
```python
from tech_sentiment_analyzer import tech_sentiment_analyzer

response = tech_sentiment_analyzer(
    user_input="Elon Musk's recent tweets show mixed sentiment about SpaceX's Mars mission."
)
print(response)
```

### Custom LLM Integration
#### Using OpenAI:
```python
from langchain_openai import ChatOpenAI
from tech_sentiment_analyzer import tech_sentiment_analyzer

llm = ChatOpenAI()
response = tech_sentiment_analyzer(
    user_input="Satya Nadella's leadership at Microsoft has been widely praised.",
    llm=llm
)
print(response)
```

#### Using Anthropic:
```python
from langchain_anthropic import ChatAnthropic
from tech_sentiment_analyzer import tech_sentiment_analyzer

llm = ChatAnthropic()
response = tech_sentiment_analyzer(
    user_input="Tim Cook's focus on privacy at Apple has sparked debates.",
    llm=llm
)
print(response)
```

#### Using Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from tech_sentiment_analyzer import tech_sentiment_analyzer

llm = ChatGoogleGenerativeAI()
response = tech_sentiment_analyzer(
    user_input="Sundar Pichai's vision for Google's AI future is ambitious.",
    llm=llm
)
print(response)
```

---

## 🔧 Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_input` | `str` | The text input to analyze for sentiment. |
| `api_key` | `Optional[str]` | LLM7 API key (defaults to `LLM7_API_KEY` environment variable). |
| `llm` | `Optional[BaseChatModel]` | Custom LLM instance (e.g., `ChatOpenAI`, `ChatAnthropic`). Defaults to `ChatLLM7`. |

---

## 🔑 API Key & Rate Limits
- **Default LLM**: Uses `ChatLLM7` (from [`langchain_llm7`](https://pypi.org/project/langchain-llm7/)).
- **Free Tier**: Sufficient for most use cases (check [LLM7 docs](https://token.llm7.io/) for limits).
- **Custom API Key**: Pass via `api_key` parameter or `LLM7_API_KEY` environment variable:
  ```python
  response = tech_sentiment_analyzer(
      user_input="Example text...",
      api_key="your_llm7_api_key"
  )
  ```

---

## 📝 Output Format
The function returns a **list of structured sentiment scores** (e.g., polarity, intensity, confidence) extracted via regex-matching. Example output:
```python
[
    {"entity": "Elon Musk", "polarity": "positive", "intensity": 0.85, "confidence": 0.92},
    {"entity": "SpaceX", "polarity": "neutral", "intensity": 0.30, "confidence": 0.88}
]
```

---

## 🛠️ Development & Support
- **GitHub Issues**: [Report bugs/feature requests](https://github.com/chigwell/tech_sentiment_analyzer/issues)
- **Author**: Eugene Evstafev ([@chigwell](https://github.com/chigwell))
- **Email**: [hi@euegne.plus](mailto:hi@euegne.plus)
- **License**: MIT (see [LICENSE](https://github.com/chigwell/tech_sentiment_analyzer/blob/main/LICENSE))

---

## 🔗 References
- **LLM7 Integration**: [`langchain_llm7`](https://pypi.org/project/langchain-llm7/)
- **Custom LLMs**: [LangChain Docs](https://docs.langchain.com/)