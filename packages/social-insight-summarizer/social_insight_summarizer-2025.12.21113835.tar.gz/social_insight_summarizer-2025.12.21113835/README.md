# social-insight-summarizer
[![PyPI version](https://badge.fury.io/py/social-insight-summarizer.svg)](https://badge.fury.io/py/social-insight-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/social-insight-summarizer)](https://pepy.tech/project/social-insight-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A package designed to analyze social media activity within an organization based on user-provided descriptions. It generates a structured summary highlighting key trends, comparisons, and insights about platform engagement levels, especially focusing on recent activity patterns versus other networks. The package leverages language models to produce clear, organized reports suitable for social media management and strategic planning.

## Installation

Install the package via pip:

```bash
pip install social_insight_summarizer
```

## Usage

Import the main function and invoke it with your input text. You can specify your own language model instance if desired, or use the default ChatLLM7 provided by the package.

```python
from social_insight_summarizer import social_insight_summarizer

# Example usage:
response = social_insight_summarizer(
    user_input="Provide a brief description of recent social media activities across platforms.",
    api_key="your_llm7_api_key"  # Optional if API key is set in environment variables
)
print(response)
```

## Parameters

- **user_input** (`str`): The descriptive text about social media activity to analyze.
- **llm** (`Optional[BaseChatModel]`): An optional custom language model instance from langchain. If not provided, the function defaults to using `ChatLLM7`.
- **api_key** (`Optional[str]`): API key for LLM7. If not supplied, the code will attempt to read from the environment variable `LLM7_API_KEY`. If absent, it defaults to `"None"`.

## Additional Details

This package uses `ChatLLM7` from the [`langchain_llm7`](https://pypi.org/project/langchain-llm7/) library. The default setup relies on its free tier, which provides sufficient rate limits for most use cases.

Dev can seamlessly integrate other language models, such as OpenAI, Anthropic, or Google Generative AI, by passing their respective instances:

```python
from langchain_openai import ChatOpenAI
from social_insight_summarizer import social_insight_summarizer

llm = ChatOpenAI()
response = social_insight_summarizer(
    user_input="Describe recent social media activity.",
    llm=llm
)
```

Similarly, for Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from social_insight_summarizer import social_insight_summarizer

llm = ChatAnthropic()
response = social_insight_summarizer(
    user_input="Describe recent social media activity.",
    llm=llm
)
```

Or Google Generative AI:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from social_insight_summarizer import social_insight_summarizer

llm = ChatGoogleGenerativeAI()
response = social_insight_summarizer(
    user_input="Describe recent social media activity.",
    llm=llm
)
```

## Support and Issues

For questions or to report issues, please visit the repository issues page:

[https://github.com/yourusername/social-insight-summarizer/issues](https://github.com/yourusername/social-insight-summarizer/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus

GitHub: [chigwell](https://github.com/chigwell)