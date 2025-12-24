# transword-matcher
[![PyPI version](https://badge.fury.io/py/transword-matcher.svg)](https://badge.fury.io/py/transword-matcher)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/transword-matcher)](https://pepy.tech/project/transword-matcher)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that uses structured pattern matching to interpret user requests for language translation, extracting the source and target languages along with the text to translate. It returns a detailed, organized response including the translated text, original text, and detected source and target languages.

## Installation

```bash
pip install transword_matcher
```

## Usage

```python
from transword_matcher import transword_matcher

# Example usage with default LLM (ChatLLM7)
response = transword_matcher(
    user_input="Translate 'hello' from English to Spanish"
)
print(response)
```

### Using a Custom LLM

You can pass your own LangChain-compatible LLM instance:

```python
from langchain_openai import ChatOpenAI
from transword_matcher import transword_matcher

llm = ChatOpenAI()
response = transword_matcher(
    user_input="Translate this text to French",
    llm=llm
)
```

```python
from langchain_anthropic import ChatAnthropic
from transword_matcher import transword_matcher

llm = ChatAnthropic()
response = transword_matcher(
    user_input="How do you say 'thank you' in Japanese?",
    llm=llm
)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from transword_matcher import transword_matcher

llm = ChatGoogleGenerativeAI()
response = transword_matcher(
    user_input="Translate from German to English: 'Guten Tag'",
    llm=llm
)
```

### Using Custom API Key

```python
from transword_matcher import transword_matcher

response = transword_matcher(
    user_input="Translate to Italian",
    api_key="your_llm7_api_key_here"
)
```

## Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): LangChain LLM instance (defaults to ChatLLM7)
- `api_key` (Optional[str]): API key for LLM7 service (if using default LLM)

## Default LLM

The package uses ChatLLM7 from [langchain_llm7](https://pypi.org/project/langchain-llm7/) by default. The free tier rate limits are sufficient for most use cases.

To get a free API key for LLM7, register at: https://token.llm7.io/

## Error Handling

The function raises a `RuntimeError` if the LLM call fails or pattern matching is unsuccessful.

## Development

Issues and contributions welcome at: https://github.com/chigwell/transword-matcher

## Author

Eugene Evstafev  
hi@euegne.plus