# SupportInsightCheck
[![PyPI version](https://badge.fury.io/py/supportinsightcheck.svg)](https://badge.fury.io/py/supportinsightcheck)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/supportinsightcheck)](https://pepy.tech/project/supportinsightcheck)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that analyzes customer service or technical support interaction descriptions to identify potential red flags that could lead to public complaints or negative exposure. The system evaluates text for issues like poor communication, unprofessional behavior, lack of accountability, or unethical practices, and returns a structured assessment with actionable feedback.

## Installation

```bash
pip install supportinsightcheck
```

## Usage

### Basic Usage

```python
from supportinsightcheck import supportinsightcheck

user_input = "The support agent was rude and refused to help me with my issue..."
results = supportinsightcheck(user_input)
print(results)
```

### Using Custom LLM

You can use any LangChain-compatible LLM by passing it to the function:

```python
from langchain_openai import ChatOpenAI
from supportinsightcheck import supportinsightcheck

llm = ChatOpenAI()
user_input = "The technician didn't show up for the scheduled appointment..."
response = supportinsightcheck(user_input, llm=llm)
```

```python
from langchain_anthropic import ChatAnthropic
from supportinsightcheck import supportinsightcheck

llm = ChatAnthropic()
user_input = "They charged me for services I didn't request..."
response = supportinsightcheck(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from supportinsightcheck import supportinsightcheck

llm = ChatGoogleGenerativeAI()
user_input = "The support representative gave me incorrect information..."
response = supportinsightcheck(user_input, llm=llm)
```

### Using Custom API Key

```python
from supportinsightcheck import supportinsightcheck

user_input = "They refused to honor their warranty policy..."
response = supportinsightcheck(user_input, api_key="your_llm7_api_key_here")
```

## Parameters

- `user_input` (str): The text description of the support interaction to analyze
- `llm` (Optional[BaseChatModel]): LangChain LLM instance (defaults to ChatLLM7)
- `api_key` (Optional[str]): API key for LLM7 service (if using default LLM)

## Default LLM Configuration

The package uses `ChatLLM7` from [langchain-llm7](https://pypi.org/project/langchain-llm7/) by default. The free tier rate limits are sufficient for most use cases. For higher rate limits, you can:

1. Set the `LLM7_API_KEY` environment variable
2. Pass your API key directly to the function
3. Get a free API key at [https://token.llm7.io/](https://token.llm7.io/)

## Error Handling

The function will raise a `RuntimeError` if the LLM call fails or if the response doesn't match the expected format.

## Contributing

Found an issue or have a suggestion? Please open an issue on [GitHub](https://github.com/chigwell/supportinsightcheck/issues).

## Author

**Eugene Evstafev**  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)

## License

This project is licensed under the MIT License - see the LICENSE file for details.