# vibe-analyzer
[![PyPI version](https://badge.fury.io/py/vibe-analyzer.svg)](https://badge.fury.io/py/vibe-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/vibe-analyzer)](https://pepy.tech/project/vibe-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


vibe-analyzer is a Python package designed to analyze user-provided text to detect and categorize the overall emotional tone or "vibe" of the content. It processes input text and returns a structured summary of the detected emotions, such as positivity, negativity, excitement, or calmness, using pattern matching to ensure consistent and reliable output formatting. This tool is useful for sentiment tracking in user feedback, social media monitoring, or enhancing chatbot interactions by adapting responses based on emotional context.

## Installation

Install vibe-analyzer via pip:

```bash
pip install vibe_analyzer
```

## Usage

Here's a basic example of how to use vibe_analyzer:

```python
from vibe_analyzer import vibe_analyzer

# Sample user input
user_input = "I'm feeling great today!"

# Analyze the vibe
result = vibe_analyzer(user_input)

print(result)
```

## Function Parameters

- **user_input**: `str`  
  The text input from the user to analyze for emotional tone.

- **llm**: `Optional[BaseChatModel]`  
  An instance of a language model to use for analysis. If not provided, the default `ChatLLM7` from `langchain_llm7` will be used.

- **api_key**: `Optional[str]`  
  Your API key for `llm7`. If not provided, it will be read from the environment variable `LLM7_API_KEY`.

## Underlying Technology

The package uses the `ChatLLM7` class from the [`langchain_llm7`](https://pypi.org/project/langchain-llm7/) library by default. Developers can easily pass their own language model instances compatible with the interface, such as:

```python
from langchain_openai import ChatOpenAI
from vibe_analyzer import vibe_analyzer

llm = ChatOpenAI()
response = vibe_analyzer(user_input, llm=llm)
```

Similarly, other models like Anthropic or Google Generative AI can be used:

```python
from langchain_anthropic import ChatAnthropic
from vibe_analyzer import vibe_analyzer

llm = ChatAnthropic()
response = vibe_analyzer(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from vibe_analyzer import vibe_analyzer

llm = ChatGoogleGenerativeAI()
response = vibe_analyzer(user_input, llm=llm)
```

## Rate Limits and API Keys

The default rate limits for LLM7's free tier are sufficient for most use cases. For higher rate limits, you can:

- Set your API key via the environment variable `LLM7_API_KEY`, or
- Pass it directly in function call: `vibe_analyzer(user_input, api_key="your_api_key")`

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Support

If you encounter issues or have questions, please open an issue on the GitHub repository:  
[https://github.com/chigwell/vibe-analyzer](https://github.com/chigwell/vibe-analyzer)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)