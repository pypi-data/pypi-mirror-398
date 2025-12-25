# Psi Fusion Insights
[![PyPI version](https://badge.fury.io/py/psi-fusion-insights.svg)](https://badge.fury.io/py/psi-fusion-insights)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/psi-fusion-insights)](https://pepy.tech/project/psi-fusion-insights)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Psi Fusion Insights is a Python package designed to extract and structure key insights from technical descriptions about PsiQuantum's fusion-based quantum computation.

## Overview
Users input text containing detailed explanations or summaries of PsiQuantum's quantum computing advancements, and the package processes this text to return a standardized, structured output. The structured response includes identified key components such as quantum fusion techniques, computational advantages, technical challenges, and potential applications.

## Installation
To install Psi Fusion Insights, run the following command:
```bash
pip install psi_fusion_insights
```

## Usage
To use the package, simply call the `psi_fusion_insights` function with the input text as a string:
```python
from psi_fusion_insights import psi_fusion_insights

user_input = "Your technical description here"
response = psi_fusion_insights(user_input)
print(response)
```
Alternatively, you can specify a `llm` instance to use, if not provided, the default `ChatLLM7` from `langchain_llm7` will be used:
```python
from langchain_llm7 import ChatLLM7
from psi_fusion_insights import psi_fusion_insights

llm = ChatLLM7()
response = psi_fusion_insights(user_input, llm=llm)
print(response)
```
If you want to use a different LLM, you can pass a `langchain` instance accordingly, for example:
```python
from langchain_openai import ChatOpenAI
from psi_fusion_insights import psi_fusion_insights

llm = ChatOpenAI()
response = psi_fusion_insights(user_input, llm=llm)
```

## Notes
* Psi Fusion Insights uses the `ChatLLM7` from `langchain_llm7` by default.
* If you want to use a different LLM, simply pass a `langchain` instance accordingly.
* The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7, you can pass your own `api_key` via environment variable `LLM7_API_KEY` or via passing it directly like `psi_fusion_insights(user_input, api_key="your_api_key")`. You can get a free API key by registering at https://token.llm7.io/

## Author
Eugene Evstafev
hi@eugene.plus
https://github.com/chigwell

## Issues
For issues with the package, please submit a pull request or open an issue at: https://github.com/chigwell/psi-fusion-insights