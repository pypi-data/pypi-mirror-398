# archaeo_summarizer
[![PyPI version](https://badge.fury.io/py/archaeo-summarizer.svg)](https://badge.fury.io/py/archaeo-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/archaeo-summarizer)](https://pepy.tech/project/archaeo-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

A package designed to extract structured summaries from textual inputs related to archaeological and historical research. Users provide descriptive or analytical text, and the package generates concise, organized summaries that highlight key findings, cultural developments, or migration patterns.

## Features

* Process complex textual sources to transform narrative data into standardized, digestible formats
* Streamline the creation of structured insights from textual inputs
* Ensure privacy and data safety by only processing text
* Support effective data comparison and analysis across studies

## Installation

```bash
pip install archaeo_summarizer
```

## Usage

```python
from archaeo_summarizer import archaeo_summarizer

response = archaeo_summarizer(
    user_input="Text to process",
    llm=None,  # Optional: Provide a langchain llm instance to use
    api_key=None  # Optional: Provide an LLM7 api key if not using the default rate limits
)
print(response)
```

You can safely pass your own llm instance (based on https://docs.langchain.com/) if you want to use a different LLM.

```python
from langchain_openai import ChatOpenAI
from archaeo_summarizer import archaeo_summarizer

llm = ChatOpenAI()
response = archaeo_summarizer(llm=llm)
print(response)
```

or for example to use the anthropic https://docs.langchain.anthropic.com/

```python
from langchain_anthropic import ChatAnthropic
from archaeo_summarizer import archaeo_summarizer

llm = ChatAnthropic()
response = archaeo_summarizer(llm=llm)
print(response)
```

or google https://docs.langchain.google.com/

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from archaeo_summarizer import archaeo_summarizer

llm = ChatGoogleGenerativeAI()
response = archaeo_summarizer(llm=llm)
print(response)
```

The default rate limits for LLM7 free tier should be sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own api key via environment variable LLM7_API_KEY or via passing it directly like `archaeo_summarizer(api_key="your_api_key")`. You can get a free api key by registering at https://token.llm7.io/.

## Credits

* Author: Eugene Evstafev
* Author Email: hi@eugene.plus
* GitHub: https://github.com/chigwell

## Issues

* GitHub Issues: https://github.com/chigwell/.../issues

## License

Please see [MIT] for license details.