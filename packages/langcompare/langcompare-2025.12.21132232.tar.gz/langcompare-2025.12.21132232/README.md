# langcompare
[![PyPI version](https://badge.fury.io/py/langcompare.svg)](https://badge.fury.io/py/langcompare)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/langcompare)](https://pepy.tech/project/langcompare)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that helps developers quickly compare programming languages (Java, JavaScript, Python, Go) for a given task or context. It analyzes your requirements and provides structured comparisons highlighting key differences, strengths, and recommendations among the languages.

## 🚀 Features
- Compare multiple languages (Java, JavaScript, Python, Go) for any development scenario
- Get structured, actionable insights without manual research
- Customizable LLM integration (supports OpenAI, Anthropic, Google, etc.)
- Simple API with sensible defaults

## 📦 Installation

```bash
pip install langcompare
```

## 🔧 Usage

### Basic Usage (uses default LLM7)
```python
from langcompare import langcompare

response = langcompare(
    user_input="I need to build a real-time chat application. What are the key differences between JavaScript and Python?"
)
print(response)
```

### Custom LLM Integration

#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from langcompare import langcompare

llm = ChatOpenAI()
response = langcompare(
    user_input="Which language is better for microservices?",
    llm=llm
)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from langcompare import langcompare

llm = ChatAnthropic()
response = langcompare(
    user_input="What are the performance characteristics of Go vs Python?",
    llm=llm
)
```

#### Using Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langcompare import langcompare

llm = ChatGoogleGenerativeAI()
response = langcompare(
    user_input="Which language has better concurrency support?",
    llm=llm
)
```

## 🔑 API Key Configuration

The package uses **LLM7** as the default LLM provider. You can configure it in two ways:

1. **Environment Variable** (recommended for security):
```bash
export LLM7_API_KEY="your_api_key_here"
```

2. **Direct Parameter**:
```python
from langcompare import langcompare

response = langcompare(
    user_input="Compare Python and Java for backend services",
    api_key="your_api_key_here"
)
```

Get a free API key at [LLM7 Token Generator](https://token.llm7.io/).

## 📊 Response Format

The function returns a list of structured comparison points, typically including:
- Language-specific strengths
- Key differences for the given use case
- Recommendations based on requirements
- Performance considerations
- Ecosystem support

## 📜 Parameters

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `user_input` | `str` | Your development scenario or requirement description | Required |
| `api_key` | `Optional[str]` | Your LLM7 API key (if not using environment variable) | `None` (uses `LLM7_API_KEY` env var) |
| `llm` | `Optional[BaseChatModel]` | Custom LLM instance (e.g., OpenAI, Anthropic) | `None` (uses default LLM7) |

## 🔄 Rate Limits

The default LLM7 free tier provides sufficient rate limits for most use cases. For higher limits, use your own API key or consider upgrading your LLM7 plan.

## 📝 Issues & Support

For issues or feature requests, please open a GitHub issue at:
[https://github.com/chigwell/langcompare/issues](https://github.com/chigwell/langcompare/issues)

## 👤 Author

- **Eugene Evstafev** ([@chigwell](https://github.com/chigwell))
- Email: [hi@eugene.plus](mailto:hi@eugene.plus)

## 📄 License

MIT License