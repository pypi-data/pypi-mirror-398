# refactor-llm-analyzer
[![PyPI version](https://badge.fury.io/py/refactor-llm-analyzer.svg)](https://badge.fury.io/py/refactor-llm-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/refactor-llm-analyzer)](https://pepy.tech/project/refactor-llm-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


refactor-llm-analyzer is a Python package designed to facilitate structured and reliable analysis of user input related to software refactoring in the context of large language models (LLMs). It processes text-based discussions or questions to extract key themes, concerns, or strategies, enabling consistent interpretation and supporting automated decision-making or knowledge extraction. The package uses pattern matching and LLM capabilities to produce structured summaries or insights from user input.

## Installation

Install the package via pip:

```bash
pip install refactor_llm_analyzer
```

## Usage

Here's an example of how to use the package:

```python
from refactor_llm_analyzer import refactor_llm_analyzer

user_input = "How can I improve the readability of my code by refactoring the functions?"
response = refactor_llm_analyzer(user_input)
print(response)
```

### Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): An optional LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, it will be retrieved from the environment variable `LLM7_API_KEY`.

### Supporting External Language Models

This package uses `ChatLLM7` from the `langchain_llm7` module by default. Developers can supply their own language model instances for flexibility and customization. Supported integrations include:

- OpenAI GPT models
- Anthropic models
- Google Generative AI

#### Example of using a custom LLM

```python
from langchain_openai import ChatOpenAI
from refactor_llm_analyzer import refactor_llm_analyzer

llm = ChatOpenAI()
response = refactor_llm_analyzer(user_input, llm=llm)
print(response)
```

```python
from langchain_anthropic import ChatAnthropic
from refactor_llm_analyzer import refactor_llm_analyzer

llm = ChatAnthropic()
response = refactor_llm_analyzer(user_input, llm=llm)
print(response)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from refactor_llm_analyzer import refactor_llm_analyzer

llm = ChatGoogleGenerativeAI()
response = refactor_llm_analyzer(user_input, llm=llm)
print(response)
```

## Rate Limits and API Keys

The default rate limits for LLM7’s free tier are sufficient for most use cases. To increase limits, pass your API key via the environment variable `LLM7_API_KEY` or directly when calling the function:

```python
response = refactor_llm_analyzer(user_input, api_key="your_api_key")
```

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Resources

- The package relies on `ChatLLM7` from [langchain_llm7](https://pypi.org/project/langchain-llm7/)
- Documentation for other supported LLMs:
  - OpenAI: https://docs.openai.com/
  - Anthropic: https://console.anthropic.com/
  - Google Generative AI: https://cloud.google.com/vertex-ai/docs

## Contact and Support

- Developer: Eugene Evstafev
- Email: hi@eugene.plus
- GitHub: [chigwell](https://github.com/chigwell)
- Issues: [GitHub Issues](https://github.com/chigwell/refactor-llm-analyzer/issues)