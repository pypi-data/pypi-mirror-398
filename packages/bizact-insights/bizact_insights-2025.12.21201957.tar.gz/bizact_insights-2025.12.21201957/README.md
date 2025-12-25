# bizact-insights
[![PyPI version](https://badge.fury.io/py/bizact-insights.svg)](https://badge.fury.io/py/bizact-insights)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/bizact-insights)](https://pepy.tech/project/bizact-insights)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


bizact-insights is a Python package designed to process text inputs related to corporate actions, such as trademark filings or product launches, and extract structured insights. It identifies key entities, actions, and contextual information from news snippets or official statements, enabling users to quickly grasp business-related developments.

## Installation

Install the package via pip:

```bash
pip install bizact_insights
```

## Usage

```python
from bizact_insights import bizact_insights

# Example usage with default LLM7
results = bizact_insights(
    user_input="Apple announced the launch of a new product line in Europe.",
)
print(results)
```

## Parameters

- `user_input` (str): The input text to analyze.
- `llm` (Optional[BaseChatModel]): An instance of a language model (e.g., from langchain). If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): API key for LLM7. If not provided, it can be set via the environment variable `LLM7_API_KEY`.

## Details

This package relies on the `ChatLLM7` class from `langchain_llm7`, which offers a straightforward interface to the LLM7 API. It can also accept custom language model instances, allowing integration with other providers such as OpenAI, Anthropic, or Google Generative AI.

### Example with custom LLMs

```python
from langchain_openai import ChatOpenAI
from bizact_insights import bizact_insights

llm = ChatOpenAI()
response = bizact_insights(user_input="Tesla reported record deliveries.", llm=llm)
print(response)
```

```python
from langchain_anthropic import ChatAnthropic
from bizact_insights import bizact_insights

llm = ChatAnthropic()
response = bizact_insights(user_input="Microsoft announced a new cloud service.", llm=llm)
print(response)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from bizact_insights import bizact_insights

llm = ChatGoogleGenerativeAI()
response = bizact_insights(user_input="Google is expanding its workspace features.", llm=llm)
print(response)
```

## Rate Limits

The default usage via LLM7's free tier offers sufficient rate limits for most purposes. For higher throughput, you can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/) and set it via the `LLM7_API_KEY` environment variable or pass it directly:

```python
results = bizact_insights(user_input="Sample text", api_key="your_api_key_here")
```

## Support & Issues

If you encounter issues or have questions, please open an issue on the [GitHub repository](https://github.com/chigwell/bizact-insights).

## Author

Eugene Evstafev  
Email: hi@euegne.plus

GitHub: [chigwell](https://github.com/chigwell)