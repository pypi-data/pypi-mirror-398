# UpdateXplorer
[![PyPI version](https://badge.fury.io/py/updatexplorer.svg)](https://badge.fury.io/py/updatexplorer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/updatexplorer)](https://pepy.tech/project/updatexplorer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to interpret and extract structured technical insights from user-submitted hardware and software update summaries.

## Features

- Processes concise text inputs about hardware support changes or driver updates
- Outputs detailed, organized reports highlighting key components affected
- Provides compatibility considerations and recommended actions
- Ensures clarity for system administrators or developers

## Installation

```bash
pip install updatexplorer
```

## Usage

```python
from updatexplorer import updatexplorer

# Example with default LLM (ChatLLM7)
response = updatexplorer("Your update summary text here")

# Example with custom LLM (OpenAI)
from langchain_openai import ChatOpenAI
llm = ChatOpenAI()
response = updatexplorer("Your update summary text here", llm=llm)

# Example with custom LLM (Anthropic)
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
response = updatexplorer("Your update summary text here", llm=llm)

# Example with custom LLM (Google)
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
response = updatexplorer("Your update summary text here", llm=llm)
```

## Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Default LLM

The package uses `ChatLLM7` from `langchain_llm7` by default. You can safely pass your own LLM instance if you want to use another LLM.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own API key via environment variable `LLM7_API_KEY` or via passing it directly like:

```python
response = updatexplorer("Your update summary text here", api_key="your_api_key")
```

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## Author

- **Eugene Evstafev**
  - GitHub: [chigwell](https://github.com/chigwell)
  - Email: hi@eugene.plus

## Issues

If you encounter any issues, please report them on the [GitHub issues page](https://github.com/chigwell/updatexplorer/issues).