# taleb-analysis
[![PyPI version](https://badge.fury.io/py/taleb-analysis.svg)](https://badge.fury.io/py/taleb-analysis)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/taleb-analysis)](https://pepy.tech/project/taleb-analysis)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

-------------

A text-based analysis package inspired by Nassim Taleb's concepts of Black Swan events and antifragility.

## Overview
------------

A new package would provide a text input describing a system, event, or scenario, and return a structured analysis based on Nassim Taleb's concepts of Black Swan events and antifragility. It would identify whether the input describes a fragile, robust, or antifragile system, highlight potential hidden risks (Black Swans), and suggest principles to improve resilience or benefit from volatility.

## Installing
------------

You can install the package using pip:
```bash
pip install taleb_analysis
```

## Usage
-----

To use the package, you can call the `taleb_analysis` function with the following parameters:
```python
from taleb_analysis import taleb_analysis

value = taleb_analysis(user_input="text to analyze", api_key=None, llm=None)
```
By default, it will use the `ChatLLM7` from `langchain_llm7` package as the LLM instance. You can pass your own `llm` instance if you prefer to use a different LLM.

For example, to use the OpenAI's LLM, you can pass it like this:
```python
from langchain_openai import ChatOpenAI
from taleb_analysis import taleb_analysis

llm = ChatOpenAI()
response = taleb_analysis(user_input="text to analyze", llm=llm)
```

Similarly, for Anthenropic:
```python
from langchain_anthropic import ChatAnthropic
from taleb_analysis import taleb_analysis

llm = ChatAnthropic()
response = taleb_analysis(user_input="text to analyze", llm=llm)
```

And for Google Generative AI:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from taleb_analysis import taleb_analysis

llm = ChatGoogleGenerativeAI()
response = taleb_analysis(user_input="text to analyze", llm=llm)
```

## API Key for ChatLLM7
-----------------------

The default rate limits for the `ChatLLM7` free tier are generally sufficient. For higher rate limits, you can provide your API key in one of the following ways:

*   Set the `LLM7_API_KEY` environment variable.
*   Pass the API key directly to the function: `taleb_analysis(user_input, api_key="your_api_key")`.

You can obtain a free API key by registering at https://token.llm7.io/

## Contributing
------------

Contributions are welcome! Please refer to the GitHub repository for more information.

## Author
---------

*   Eugene Evstafev (hi@eugene.plus)

## GitHub
---------

*   [taleb-analysis GitHub Issues](https://github.com/chigwell/taleb-analysis/issues)