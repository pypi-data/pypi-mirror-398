# AI Reliability Analyzer
[![PyPI version](https://badge.fury.io/py/ai-reliability-analyzer.svg)](https://badge.fury.io/py/ai-reliability-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ai-reliability-analyzer)](https://pepy.tech/project/ai-reliability-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

The `ai_reliability_analyzer` package is designed to analyze user queries about AI tool reliability and generate structured insights. It takes a text input, such as a question or comment about AI code editor performance issues, and uses a Language Model (LLM) to produce a categorized breakdown of potential reasons (e.g., latency, model limitations, integration challenges). The output is formatted for easy parsing, ensuring consistency and actionable feedback without delving into sensitive or restricted topics.

## Features

- Analyzes user queries about AI tool reliability.
- Generates structured insights and categorizes potential reasons.
- Supports custom LLM instances for flexibility.
- Defaults to using `ChatLLM7` from `langchain_llm7` if no LLM instance is provided.
- Ensures output consistency and actionable feedback.

## Installation

You can install the package using pip:

```bash
pip install ai_reliability_analyzer
```

## Usage

### Basic Usage

```python
from ai_reliability_analyzer import ai_reliability_analyzer

user_input = "Why is my AI code editor so slow?"
response = ai_reliability_analyzer(user_input)
print(response)
```

### Using a Custom LLM Instance

You can use a custom LLM instance by passing it to the function. For example, to use `ChatOpenAI` from `langchain_openai`:

```python
from langchain_openai import ChatOpenAI
from ai_reliability_analyzer import ai_reliability_analyzer

llm = ChatOpenAI()
user_input = "Why is my AI code editor so slow?"
response = ai_reliability_analyzer(user_input, llm=llm)
print(response)
```

Similarly, you can use other LLM instances like `ChatAnthropic` or `ChatGoogleGenerativeAI`:

```python
from langchain_anthropic import ChatAnthropic
from ai_reliability_analyzer import ai_reliability_analyzer

llm = ChatAnthropic()
user_input = "Why is my AI code editor so slow?"
response = ai_reliability_analyzer(user_input, llm=llm)
print(response)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from ai_reliability_analyzer import ai_reliability_analyzer

llm = ChatGoogleGenerativeAI()
user_input = "Why is my AI code editor so slow?"
response = ai_reliability_analyzer(user_input, llm=llm)
print(response)
```

### Using a Custom API Key

If you want to use a custom API key for `ChatLLM7`, you can pass it directly or set it via the environment variable `LLM7_API_KEY`:

```python
from ai_reliability_analyzer import ai_reliability_analyzer

user_input = "Why is my AI code editor so slow?"
api_key = "your_custom_api_key"
response = ai_reliability_analyzer(user_input, api_key=api_key)
print(response)
```

Or set the environment variable:

```bash
export LLM7_API_KEY="your_custom_api_key"
```

Then use the package without passing the API key:

```python
from ai_reliability_analyzer import ai_reliability_analyzer

user_input = "Why is my AI code editor so slow?"
response = ai_reliability_analyzer(user_input)
print(response)
```

## Rate Limits

The default rate limits for the LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly in the function call.

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/ai-reliability-analyzer).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)