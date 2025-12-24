# AI Design Insights Package
[![PyPI version](https://badge.fury.io/py/ai-design-insights.svg)](https://badge.fury.io/py/ai-design-insights)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ai-design-insights)](https://pepy.tech/project/ai-design-insights)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


AI Design Insights is a Python package that helps extract, categorize, and structure insights from discussions, articles, or forums about AI system design challenges. It leverages language models to identify key pain points such as scalability issues, integration complexities, or ethical considerations, facilitating easier analysis and targeted problem-solving.

## Installation

Install the package via pip:

```bash
pip install ai_design_insights
```

## Usage

Import the main function and use it to process your input text. You can use the default language model, ChatLLM7 from langchain_llm7, or pass your own instance of a compatible language model for more flexibility.

```python
from ai_design_insights import ai_design_insights

# Example with default LLM
response = ai_design_insights(user_input="Your discussion or article text here")
```

## Customizing LLM

By default, the package uses ChatLLM7 (from langchain_llm7) with environment variable or direct API key configuration. If you prefer to use another language model, simply instantiate it and pass it as an argument.

### Using your own LLM instance

**OpenAI example:**

```python
from langchain_openai import ChatOpenAI
from ai_design_insights import ai_design_insights

llm = ChatOpenAI()
response = ai_design_insights(user_input="Your text here", llm=llm)
```

**Anthropic example:**

```python
from langchain_anthropic import ChatAnthropic
from ai_design_insights import ai_design_insights

llm = ChatAnthropic()
response = ai_design_insights(user_input="Your text here", llm=llm)
```

**Google Generative AI example:**

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from ai_design_insights import ai_design_insights

llm = ChatGoogleGenerativeAI()
response = ai_design_insights(user_input="Your text here", llm=llm)
```

## Configuration

The package uses the default free-tier rate limits of LLM7, which are sufficient for most use cases. For higher rate limits, set your API key via environment variable:

```bash
export LLM7_API_KEY="your_api_key"
```

or pass it directly during function call:

```python
response = ai_design_insights(user_input, api_key="your_api_key")
```

You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Compatibility

This package relies on the `langchain_llm7` library ([PyPI link](https://pypi.org/project/langchain_llm7/)) and supports any compatible language model instance, including OpenAI, Anthropic, Google, and others, provided they follow the langchain interface.

## Support and Issue Tracking

For issues, bugs, or feature requests, please visit:

[https://github.com/chigwell/ai-design-insights/issues](https://github.com/chigwell/ai-design-insights/issues)

## Author

Eugene Evstafev

Email: hi@euegne.plus

GitHub: [chigwell](https://github.com/chigwell)