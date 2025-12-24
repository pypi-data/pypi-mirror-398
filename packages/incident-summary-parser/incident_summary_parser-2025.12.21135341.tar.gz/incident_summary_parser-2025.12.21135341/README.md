# Incident Summary Parser Package
[![PyPI version](https://badge.fury.io/py/incident-summary-parser.svg)](https://badge.fury.io/py/incident-summary-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/incident-summary-parser)](https://pepy.tech/project/incident-summary-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


This Python package provides a simple and reliable way to analyze and extract structured incident summaries from unstructured text reports or news snippets. It leverages large language models (LLMs) to interpret incident descriptions and outputs standardized information, making it easy to integrate incident analysis into your workflow or applications.

## Installation

Install the package via pip:

```bash
pip install incident_summary_parser
```

## Usage

Import and utilize the `incident_summary_parser` function as follows:

```python
from incident_summary_parser import incident_summary_parser

response = incident_summary_parser(
    user_input="Your incident report text here",
    api_key="your_llm7_api_key",  # optional if set via environment variable
    llm=None  # optional, can pass your own LLM instance
)
print(response)
```

### Parameters

- `user_input` (str):
  The incident report or news snippet you want to analyze.

- `llm` (Optional[BaseChatModel]):
  An optional language model instance conforming to `langchain`'s interface. If not provided, the function defaults to using `ChatLLM7`.

- `api_key` (Optional[str]):
  Your API key for the LLM7 service. Can also be set via the environment variable `LLM7_API_KEY`.

### Supporting Custom LLMs

You can pass your own LLM implementations, such as OpenAI, Anthropic, or Google's Generative AI, to the function for flexibility, for example:

```python
from langchain_openai import ChatOpenAI
from incident_summary_parser import incident_summary_parser

llm = ChatOpenAI()
response = incident_summary_parser(
    user_input="Sample incident report",
    llm=llm
)
```

Or with other providers:

```python
from langchain_anthropic import ChatAnthropic
from incident_summary_parser import incident_summary_parser

llm = ChatAnthropic()
response = incident_summary_parser(
    user_input="Sample incident report",
    llm=llm
)
```

## Notes

- The package uses `ChatLLM7` from `langchain_llm7` (see [PyPI](https://pypi.org/project/langchain-llm7/)) by default.
- Default rate limits are suitable for most use cases, but you can increase limits by obtaining your own API key.
- You can register for a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Contributing

Please report issues or contribute improvements via the GitHub repository: [https://github....](https://github.com/...).

## Author

- **Name:** Eugene Evstafev  
- **Email:** hi@eugene.plus  
- **GitHub:** chigwell