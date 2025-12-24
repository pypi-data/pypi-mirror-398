# yearly_insights_parser
[![PyPI version](https://badge.fury.io/py/yearly-insights-parser.svg)](https://badge.fury.io/py/yearly-insights-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/yearly-insights-parser)](https://pepy.tech/project/yearly-insights-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

## Overview
A new package that analyzes user-provided text summaries of yearly breakdowns (e.g., financial reports, project post-mortems, or performance reviews) and extracts structured insights. It uses an LLM to identify key themes, recurring issues, successes, and recommendations, then formats the output into a consistent, machine-readable structure. This helps users quickly digest and act on summarized yearly data without manual parsing.

## Installation
```bash
pip install yearly_insights_parser
```
## Usage
```python
from yearly_insights_parser import yearly_insights_parser

response = yearly_insights_parser(
    user_input="...",  # user-provided text input
    api_key="your_api_key",  # optional, use LLM7 API key for higher rate limits
    llm=your_llm_instance,  # optional, use a custom LLM instance
)
```
The `yearly_insights_parser` function takes three parameters:

*   `user_input`: the text input to process (string)
*   `api_key`: optional, use an LLM7 API key for higher rate limits (string)
*   `llm`: optional, use a custom LLM instance (BaseChatModel instance)

By default, it uses the ChatLLM7 from `langchain_llm7 <https://pypi.org/project/langchain-llm7/>`_. If you want to use another LLM, you can pass your own instance:
```python
from langchain_openai import ChatOpenAI
from yearly_insights_parser import yearly_insights_parser

llm = ChatOpenAI()
response = yearly_insights_parser(user_input="...", llm=llm)
```
Similarly, you can use `ChatAnthropic` or `ChatGoogleGenerativeAI` from `langchain_anthropic <https://pypi.org/project/langchain-anthropic/>`_ or `langchain_google_genai <https://pypi.org/project/langchain-google-genai/>`_ respectively.

Note that the default rate limits for LLM7 free tier should be sufficient for most use cases. If you need higher rate limits, you can provide your own API key using one of the above methods.

## API Key for LLM7
The default rate limits for the LLM7 free tier are generally sufficient for most use cases. If you require higher rate limits for LLM7, you can provide your own API key:

*   Via the `LLM7_API_KEY` environment variable.
*   Directly by passing the `api_key` argument to the function: `yearly_insights_parser(user_input="...", api_key="your_api_key")`
You can obtain a free API key by registering at `https://token.llm7.io/`

## Contributing
Please report any issues or suggestions on the GitHub issues page: <https://github.com/chigwell/yearly-insights-parser/>

## Author
*   Eugene Evstafev (hi@eugene.plus)

## License
[MIT License] - see the LICENSE.md file for details.