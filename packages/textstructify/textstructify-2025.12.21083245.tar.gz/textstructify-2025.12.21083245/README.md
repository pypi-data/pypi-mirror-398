# textstructify

![PyPI version](https://badge.fury.io/py/textstructify.png) ![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg) ![Downloads](https://img.shields.io/pypi/dm/textstructify) ![LinkedIn](https://img.shields.io/badge/LinkedIn-Eugene%20Evstafev-blue)

textstructify is a Python package designed to transform raw text inputs into structured, meaningful outputs using advanced language models. It leverages the llmatch-messages framework to ensure responses are consistent and properly formatted. Ideal for applications requiring extraction of key points, summaries, or specific text formatting.

## Installation

Install from PyPI:

```bash
pip install textstructify
```

## Usage

Import the package and call the main function as shown:

```python
from textstructify import textstructify

response = textstructify(
    user_input="Your raw text input here",
    api_key="your_llm7_api_key"  # optional if LLM is specified
)
print(response)
```

### Parameters

- **user_input** (str): The input text string to process.
- **llm** (Optional[BaseChatModel]): An instance of a language model from langchain. If None, the default ChatLLM7 is used.
- **api_key** (Optional[str]): API key for LLM7. If not provided, will attempt to read from environment variable `LLM7_API_KEY` or will use the default.

### Using custom LLMs

You can pass your own LLM instances compatible with langchain. For example:

```python
from langchain_openai import ChatOpenAI
from textstructify import textstructify

llm = ChatOpenAI()
response = textstructify(user_input="Your text here", llm=llm)
```

Similarly, with other supported LLMs like Anthropic or Google Generative AI:

```python
from langchain_anthropic import ChatAnthropic
from textstructify import textstructify

llm = ChatAnthropic()
response = textstructify(user_input="Your text here", llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from textstructify import textstructify

llm = ChatGoogleGenerativeAI()
response = textstructify(user_input="Your text here", llm=llm)
```

## Notes

- The default rate limits for LLM7's free tier are sufficient for most use cases.
- For higher rate limits, supply an API key via environment variable `LLM7_API_KEY` or directly in the function call.
- Obtain a free API key at https://token.llm7.io/.

## References

- [llmatch-messages](https://pypi.org/project/llmatch-messages/)
- [langchain](https://python.langchain.com/)
- [ChatLLM7](https://pypi.org/project/chatllm7/)

## Author

Eugene Evstafev  
Email: hi@eugene.plus  
GitHub: [chigwell](https://github.com/chigwell)  

## Issue Tracker

Report issues at: https://github.com/chigwell/textstructify/issues