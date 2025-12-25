# Logistics Headline Extractor
[![PyPI version](https://badge.fury.io/py/logistics-headline-extractor.svg)](https://badge.fury.io/py/logistics-headline-extractor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/logistics-headline-extractor)](https://pepy.tech/project/logistics-headline-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for transforming unstructured news headlines or short text snippets into structured, domain-specific summaries. Ideal for business, logistics, and transportation sectors, this tool extracts key details (e.g., entity, action, reason, location, and impact) and outputs them in a standardized JSON-like format.

## Features

- Extracts structured information from noisy text inputs
- Outputs results in a consistent JSON-like format
- Supports custom LLM backends via LangChain
- Easy integration with existing workflows

## Installation

Install the package via pip:

```bash
pip install logistics_headline_extractor
```

## Usage

### Basic Example

```python
from logistics_headline_extractor import logistics_headline_extractor

user_input = "Waymo temporarily suspends service in SF amid power outage"
result = logistics_headline_extractor(user_input=user_input)
print(result)
```

### Using a Custom LLM

You can use any LangChain-compatible LLM by passing it to the `llm` parameter:

#### OpenAI Example
```python
from langchain_openai import ChatOpenAI
from logistics_headline_extractor import logistics_headline_extractor

llm = ChatOpenAI()
user_input = "Waymo temporarily suspends service in SF amid power outage"
result = logistics_headline_extractor(user_input=user_input, llm=llm)
```

#### Anthropic Example
```python
from langchain_anthropic import ChatAnthropic
from logistics_headline_extractor import logistics_headline_extractor

llm = ChatAnthropic()
user_input = "Waymo temporarily suspends service in SF amid power outage"
result = logistics_headline_extractor(user_input=user_input, llm=llm)
```

#### Google Generative AI Example
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from logistics_headline_extractor import logistics_headline_extractor

llm = ChatGoogleGenerativeAI()
user_input = "Waymo temporarily suspends service in SF amid power outage"
result = logistics_headline_extractor(user_input=user_input, llm=llm)
```

### Using Custom API Key

For LLM7 (default provider), you can provide your API key:

```python
from logistics_headline_extractor import logistics_headline_extractor

user_input = "Waymo temporarily suspends service in SF amid power outage"
result = logistics_headline_extractor(user_input=user_input, api_key="your_api_key_here")
```

Or set it as an environment variable:
```bash
export LLM7_API_KEY="your_api_key_here"
```

## Parameters

- `user_input` (str): The text input to process
- `llm` (Optional[BaseChatModel]): LangChain LLM instance (defaults to ChatLLM7)
- `api_key` (Optional[str]): API key for LLM7 (if using default provider)

## Default LLM Provider

This package uses [ChatLLM7](https://pypi.org/project/langchain-llm7/) by default. The free tier rate limits are sufficient for most use cases. For higher rate limits, you can:

1. Get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)
2. Pass your API key via the `api_key` parameter or `LLM7_API_KEY` environment variable
3. Use a different LLM provider by passing a custom LangChain LLM instance

## Output Format

The package returns a list of strings matching the pattern:
```json
{"entity": "...", "action": "...", "reason": "...", "location": "...", "temporal": "..."}
```

## Error Handling

If the LLM call fails, the function will raise a `RuntimeError` with details about the failure.

## Support

For issues and feature requests, please create an issue on our [GitHub repository](https://github.com/chigwell/logistics-headline-extractor).

## Author

**Eugene Evstafev**  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)