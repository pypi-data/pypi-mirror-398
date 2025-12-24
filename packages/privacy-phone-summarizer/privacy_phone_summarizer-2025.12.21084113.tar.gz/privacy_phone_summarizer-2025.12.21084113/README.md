# Privacy Phone Summarizer
[![PyPI version](https://badge.fury.io/py/privacy-phone-summarizer.svg)](https://badge.fury.io/py/privacy-phone-summarizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/privacy-phone-summarizer)](https://pepy.tech/project/privacy-phone-summarizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

The `privacy_phone_summarizer` package is designed to receive a short textual description of a phone company that deliberately avoids collecting personal data. It returns a structured, machine-readable summary (e.g., JSON) of the service. The package uses `llmatch-messages` to enforce a predefined response format, extracting fields such as "company_name," "privacy_policy," "key_features," and "usage_guidelines." By handling only pre-extracted text (no raw audio, video, URLs), it ensures consistent, privacy-focused output that can be easily integrated into downstream applications or dashboards.

## Installation

You can install the package using pip:

```bash
pip install privacy_phone_summarizer
```

## Usage

Here is an example of how to use the `privacy-phone-summarizer` package:

```python
from privacy_phone_summarizer import privacy_phone_summarizer

# Example user input
user_input = "Company XYZ offers a privacy-focused phone service with no data collection."

# Call the summarizer function
response = privacy_phone_summarizer(user_input)

# Print the response
print(response)
```

### Input Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the default API key will be used.

### Using a Custom LLM

You can pass your own LLM instance if you want to use a different LLM. For example, to use OpenAI:

```python
from langchain_openai import ChatOpenAI
from privacy_phone_summarizer import privacy_phone_summarizer

# Initialize the custom LLM
llm = ChatOpenAI()

# Call the summarizer function with the custom LLM
response = privacy_phone_summarizer(user_input, llm=llm)

# Print the response
print(response)
```

Similarly, you can use other LLMs like Anthropic or Google:

```python
from langchain_anthropic import ChatAnthropic
from privacy_phone_summarizer import privacy_phone_summarizer

# Initialize the custom LLM
llm = ChatAnthropic()

# Call the summarizer function with the custom LLM
response = privacy_phone_summarizer(user_input, llm=llm)

# Print the response
print(response)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from privacy_phone_summarizer import privacy_phone_summarizer

# Initialize the custom LLM
llm = ChatGoogleGenerativeAI()

# Call the summarizer function with the custom LLM
response = privacy_phone_summarizer(user_input, llm=llm)

# Print the response
print(response)
```

### API Key

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via the environment variable `LLM7_API_KEY` or directly:

```python
response = privacy_phone_summarizer(user_input, api_key="your_api_key")
```

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/privacy-phone-summarizer).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)