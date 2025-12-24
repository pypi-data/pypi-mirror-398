# claim-vet
[![PyPI version](https://badge.fury.io/py/claim-vet.svg)](https://badge.fury.io/py/claim-vet)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/claim-vet)](https://pepy.tech/project/claim-vet)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


claim-vet is a package designed to help organizations quickly identify and assess potentially false or misleading notices filed by companies such as Flock and Cyble Inc. It streamlines the process of analyzing notice or complaint texts using advanced language models, providing structured insights into the nature of the notices, indicators of falsity, and suggested next steps.

## Installation

You can install claim-vet via pip:

```bash
pip install claim_vet
```

## Usage

Here's a basic example of how to use claim_vet in your Python code:

```python
from claim_vet import claim_vet

user_input = "Your notice or complaint text goes here..."
response = claim_vet(user_input)
print(response)
```

### Parameters

- **user_input** (`str`): The text content describing the notice or complaint to analyze.
- **llm** (`Optional[BaseChatModel]`): A Langchain language model instance to use for processing. If not provided, the default `ChatLLM7` will be used.
- **api_key** (`Optional[str]`): API key for LLM7. If not provided, the function will attempt to retrieve it from the environment variable `LLM7_API_KEY`. You can also pass it directly as an argument.

### Custom LLM Usage

You can pass your own language model instance (e.g., OpenAI, Anthropic, Google) by creating it with the respective library and passing it to the `claim_vet` function:

```python
from langchain_openai import ChatOpenAI
from claim_vet import claim_vet

llm = ChatOpenAI()
response = claim_vet(user_input, llm=llm)
```

Other supported models include:

```python
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = claim_vet(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = claim_vet(user_input, llm=llm)
```

### Environment and API Keys

The default setup uses the `ChatLLM7` from `langchain_llm7`, which has sufficient free-tier rate limits for most purposes. To extend usage, obtain an API key from [Llm7 Token Service](https://token.llm7.io/) and set it via environment:

```bash
export LLM7_API_KEY='your_api_key'
```

Or pass directly:

```python
response = claim_vet(user_input, api_key='your_api_key')
```

## Development and Contribution

Contributions are welcome! Please raise issues or pull requests on the GitHub repository.

## Support

For issues or questions, contact the author at:  
**Name:** Eugene Evstafev  
**Email:** hi@euegne.plus

## Repository

Find the project and report issues at:  
https://github.com/chigwell/claim-vet