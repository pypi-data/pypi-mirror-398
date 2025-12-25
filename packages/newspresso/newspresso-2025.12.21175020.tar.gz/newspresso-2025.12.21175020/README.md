# newspresso
[![PyPI version](https://badge.fury.io/py/newspresso.svg)](https://badge.fury.io/py/newspresso)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/newspresso)](https://pepy.tech/project/newspresso)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package for processing text-based news or announcement summaries using structured LLM interactions. It extracts key details—such as effective dates, criteria adjustments, and impacted metrics—from text inputs, ensuring consistent and reliable output for media analysis or reporting workflows.

## Installation

Install the package via pip:

```bash
pip install newspresso
```

## Usage

Import the `newspresso` function and pass your text to process:

```python
from newspresso import newspresso

user_input = "Your news or announcement text here..."
result = newspresso(user_input)
print(result)
```

### Parameters

- `user_input` (str): The text input to process (e.g., news summary or announcement).
- `llm` (Optional[BaseChatModel]): A LangChain LLM instance. If not provided, the default `ChatLLM7` is used.
- `api_key` (Optional[str]): API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` is used, or a default key is attempted.

### Using a Custom LLM

You can use any LangChain-compatible LLM by passing it to the `llm` parameter. For example:

#### Using OpenAI
```python
from langchain_openai import ChatOpenAI
from newspresso import newspresso

llm = ChatOpenAI()
response = newspresso(user_input, llm=llm)
```

#### Using Anthropic
```python
from langchain_anthropic import ChatAnthropic
from newspresso import newspresso

llm = ChatAnthropic()
response = newspresso(user_input, llm=llm)
```

#### Using Google
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from newspresso import newspresso

llm = ChatGoogleGenerativeAI()
response = newspresso(user_input, llm=llm)
```

### API Key for Default LLM7

The default LLM (`ChatLLM7`) is provided via the `langchain_llm7` package (see [PyPI](https://pypi.org/project/langchain-llm7/)). The free tier rate limits are sufficient for most use cases. For higher limits, provide your own API key:

- Set the environment variable: `LLM7_API_KEY="your_api_key"`
- Or pass directly: `newspresso(user_input, api_key="your_api_key")`

Get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Example

```python
from newspresso import newspresso

news_text = """
YouTube announced changes to its chart inclusion rules effective January 2025. 
Streams will now require a minimum of 1,000 plays per track, up from 500. 
These updates impact the U.S. Billboard Charts and global metrics.
"""

details = newspresso(news_text)
print(details)
# Output may include: ['effective_date: January 2025', 'criteria_adjustment: minimum streams increased to 1000', ...]
```

## Dependencies

- `langchain_core`
- `langchain_llm7` (for default LLM)
- `llmatch_messages` (for pattern matching)

## Issues

Report issues or contribute via GitHub: [https://github.com/chigwell/newspresso](https://github.com/chigwell/newspresso)

## Author

Eugene Evstafev – hi@euegne.plus