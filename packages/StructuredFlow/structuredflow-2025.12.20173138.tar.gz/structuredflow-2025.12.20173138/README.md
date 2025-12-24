# StructuredFlow Package

StructuredFlow is a Python library designed to facilitate structured, reliable interactions with language models for summarizing and analyzing user input text. It applies predefined patterns to extract key information or insights from raw or pre-processed text data, producing consistently formatted summaries or reports. This makes it ideal for workflows such as process documentation, content summarization, or data extraction, where accuracy and repeatability are essential.

## Features
- Utilizes advanced language models for text analysis
- Applies regex patterns to extract structured data
- Ensures consistent output formatting
- Supports customization with user-provided LLM instances

## Installation

Install the package via pip:

```bash
pip install StructuredFlow
```

## Usage

### Basic example

```python
from StructuredFlow import StructuredFlow

# Example: Extract patterns from user input
results = StructuredFlow(user_input="Your text data here")
print(results)
```

### Using the default LLM (ChatLLM7)

By default, StructuredFlow uses ChatLLM7 from `langchain_llm7`, available on PyPI:

```python
from StructuredFlow import StructuredFlow

response = StructuredFlow(user_input="Your data here")
print(response)
```

### Using a custom LLM instance

You can pass your own LLM instance, such as OpenAI, Anthropic, or Google models, by importing and initializing the respective classes:

```python
# Example with OpenAI
from langchain_openai import ChatOpenAI
from StructuredFlow import StructuredFlow

llm = ChatOpenAI()
response = StructuredFlow(user_input="Your data here", llm=llm)
print(response)
```

```python
# Example with Anthropic
from langchain_anthropic import ChatAnthropic
from StructuredFlow import StructuredFlow

llm = ChatAnthropic()
response = StructuredFlow(user_input="Your data here", llm=llm)
print(response)
```

```python
# Example with Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI
from StructuredFlow import StructuredFlow

llm = ChatGoogleGenerativeAI()
response = StructuredFlow(user_input="Your data here", llm=llm)
print(response)
```

## Rate Limits and API Keys

The default rate limits for the LLM7 free tier are sufficient for most use cases. To access higher rate limits, you can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/) and set it via:

- Environment variable: `LLM7_API_KEY`
- Or directly when calling the function:

```python
response = StructuredFlow(user_input="Your data here", api_key="your_api_key")
```

## Support and Contributions

For issues, feature requests, or contributions, please visit the GitHub repository: [https://github.com/your-repo-link](https://github.com/your-repo-link)

## Author

Eugene Evstafev  
Email: hi@euegne.plus

---

**Note:** This package relies on the `langchain_llm7` library available at [PyPI](https://pypi.org/project/langchain-llm7/). Ensure you have the necessary dependencies installed and configured.