# textcurator-llm-py
[![PyPI version](https://badge.fury.io/py/textcurator-llm-py.svg)](https://badge.fury.io/py/textcurator-llm-py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/textcurator-llm-py)](https://pepy.tech/project/textcurator-llm-py)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for processing user-provided texts, such as headlines or short descriptions, and generating structured summaries or categorizations using language models. Designed to facilitate content curation, news aggregation, and event highlighting by producing consistent, formatted outputs with key information extracted automatically.

## Features

- Accepts various text inputs and outputs structured summaries.
- Uses the `ChatLLM7` model from the `langchain_llm7` package by default.
- Supports custom language model instances for increased flexibility.
- Implements regex-based pattern matching to extract data reliably.
- Suitable for applications like newsletters, databases, and alert systems.

## Installation

Install the package via pip:

```bash
pip install textcurator_llm_py
```

## Usage

Import the main function and invoke it with your input text. You can specify your preferred LLM instance or rely on the default `ChatLLM7`. If not provided, the package will use the API key from the environment variable `LLM7_API_KEY`.

```python
from textcurator_llm_py import textcurator_llm_py

results = textcurator_llm_py(
    user_input="City's Best Winter Show Is in Its Pitch-Dark Skies",
    api_key="your_api_key_here"  # optional, if not set in environment
)
print(results)
```

### Using a custom language model

You can pass your own LLM instance, such as `ChatOpenAI`, `ChatAnthropic`, or others, to tailor the processing:

```python
from langchain_openai import ChatOpenAI
from textcurator_llm_py import textcurator_llm_py

llm = ChatOpenAI()
results = textcurator_llm_py(
    user_input="Example headline about an upcoming event.",
    llm=llm
)
print(results)
```

Similarly, support exists for other LLMs:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic()
results = textcurator_llm_py(
    user_input="News about recent developments.",
    llm=llm
)
print(results)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI()
results = textcurator_llm_py(
    user_input="Short description of an event.",
    llm=llm
)
print(results)
```

## Configuration

The function optionally accepts an `api_key` parameter for the `ChatLLM7` model. If not provided, it defaults to the environment variable `LLM7_API_KEY`. For higher rate limits, obtain an API key at [https://token.llm7.io/](https://token.llm7.io/) and set it accordingly.

## Limitations

- The package relies on regex patterns defined within the source code (`pattern`). Ensure these patterns are suitable for your input data.
- The default `ChatLLM7` model is suitable for most use cases; however, users can provide custom LLMs for broader compatibility.

## Issues and Support

For issues, please visit the GitHub repository: [https://github.com/chigwell/textcurator-llm-py](https://github.com/chigwell/textcurator-llm-py)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)