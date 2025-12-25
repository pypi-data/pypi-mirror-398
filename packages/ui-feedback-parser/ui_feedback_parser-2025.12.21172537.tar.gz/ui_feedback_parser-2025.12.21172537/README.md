# ui-feedback-parser
[![PyPI version](https://badge.fury.io/py/ui-feedback-parser.svg)](https://badge.fury.io/py/ui-feedback-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/ui-feedback-parser)](https://pepy.tech/project/ui-feedback-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package designed to analyze user-submitted discussions or problem descriptions about improving business interfaces. This tool processes input text and outputs structured summaries highlighting key issues, suggested improvements, or actionable insights, helping teams quickly understand and address user feedback.

## Installation

```bash
pip install ui_feedback_parser
```

## Usage

The main function `ui_feedback_parser` takes user input text and returns a list of extracted insights:

```python
from ui_feedback_parser import ui_feedback_parser

# Basic usage with default LLM7
user_input = "The Chase Travel app's booking process is confusing. I couldn't find the filter options for flights."
result = ui_feedback_parser(user_input)
print(result)
# Output: ["Booking process is confusing", "Missing filter options for flights"]
```

### Parameters

- `user_input` (str): The user input text to process
- `llm` (Optional[BaseChatModel]): A Langchain LLM instance to use. If not provided, defaults to ChatLLM7
- `api_key` (Optional[str]): API key for LLM7. If not provided, uses the `LLM7_API_KEY` environment variable or defaults to free tier

### Using Different LLM Providers

You can use other LLM providers by passing a Langchain Chat model instance:

```python
# Using OpenAI
from langchain_openai import ChatOpenAI
from ui_feedback_parser import ui_feedback_parser

llm = ChatOpenAI()
result = ui_feedback_parser("The app's search function is too slow", llm=llm)

# Using Anthropic
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic()
result = ui_feedback_parser("The checkout process has too many steps", llm=llm)

# Using Google
from langchain_google_genai import ChatGoogleGenerativeAI
llm = ChatGoogleGenerativeAI()
result = ui_feedback_parser("The dashboard doesn't show my recent trips", llm=llm)
```

### API Key Configuration

The default rate limits for LLM7's free tier are sufficient for most use cases. For higher rate limits:

1. Set the environment variable:
```bash
export LLM7_API_KEY="your_api_key_here"
```

2. Or pass the key directly:
```python
result = ui_feedback_parser(user_input, api_key="your_api_key_here")
```

Get a free API key at [https://token.llm7.io/](https://token.llm7.io/)

## Contributing

Report issues or suggest improvements on our [GitHub issues page](https://github.com/chigwell/ui-feedback-parser/issues).

## Author

**Eugene Evstafev**  
Email: [hi@eugene.plus](mailto:hi@eugene.plus)  
GitHub: [chigwell](https://github.com/chigwell)