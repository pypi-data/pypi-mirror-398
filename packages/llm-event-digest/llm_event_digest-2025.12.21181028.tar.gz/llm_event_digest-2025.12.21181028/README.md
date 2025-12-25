# LLM Event Digest
[![PyPI version](https://badge.fury.io/py/llm-event-digest.svg)](https://badge.fury.io/py/llm-event-digest)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/llm-event-digest)](https://pepy.tech/project/llm-event-digest)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


LLM Event Digest is a Python package designed to process news headlines or short text inputs and generate structured summaries of events, such as service disruptions or incidents. Utilizing a language model, it extracts key details like the involved company, the nature of the disruption, and the cause, ensuring outputs conform to a predefined format for consistency and reliability. This tool is ideal for automated news monitoring, alert systems, or data aggregation where structured, error-free information extraction from text is required.

## Installation

Install the package via pip:

```bash
pip install llm_event_digest
```

## Usage

Here's an example of how to use the package in Python:

```python
from llm_event_digest import llm_event_digest

response = llm_event_digest(
    user_input="The internet service in downtown was down for 3 hours caused by a fiber cut.",
    api_key="your-llm7-api-key"  # Optional, if not set in environment variables
)
print(response)
```

## Parameters

- `user_input` (str): The text input (news headline or short description) to process.
- `llm` (Optional[BaseChatModel]): An optional LangChain language model instance. If not provided, the default `ChatLLM7` is used.
- `api_key` (Optional[str]): API key for LLM7. If not provided, it looks for the `LLM7_API_KEY` environment variable.

## Supported LLMs

The package uses `ChatLLM7` from [`langchain_llm7`](https://pypi.org/project/langchain-llm7) by default. 

You can also pass your own LLM instance, such as:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI()
response = llm_event_digest(
    user_input="Network outage in the city center.",
    llm=llm
)
```

Or:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic()
response = llm_event_digest(
    user_input="Server downtime due to maintenance.",
    llm=llm
)
```

And:

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI()
response = llm_event_digest(
    user_input="Scheduled power outage.",
    llm=llm
)
```

## Rate Limits

Default rate limits for LLM7 free tier are suitable for most use cases. For higher usage, obtain an API key from [https://token.llm7.io/](https://token.llm7.io/) and pass it via environment variable `LLM7_API_KEY` or directly in the function call.

## Support and Issues

If you encounter any issues or have questions, please open an issue on the GitHub repository: [https://github.com/chigwell/llm-event-digest/issues](https://github.com/chigwell/llm-event-digest/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)