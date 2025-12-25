# Git LLM Troubleshoot
[![PyPI version](https://badge.fury.io/py/git-llm-troubleshoot.svg)](https://badge.fury.io/py/git-llm-troubleshoot)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/git-llm-troubleshoot)](https://pepy.tech/project/git-llm-troubleshoot)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Git LLM Troubleshoot is a package designed to help users troubleshoot and resolve common Git mistakes. Users can describe their Git-related issues in plain text, and the package will use `llmatch-messages` to provide structured, step-by-step solutions. The system guides users through fixing errors, understanding Git commands, and recovering from accidental changes, ensuring they can confidently manage their version control workflows.

## Features

- **Plain Text Input:** Describe your Git-related issues in plain text.
- **Structured Solutions:** Receive step-by-step solutions tailored to your specific problem.
- **Flexible LLM Integration:** Use the default `ChatLLM7` from `langchain_llm7` or integrate with other LLMs like OpenAI, Anthropic, or Google.

## Installation

You can install the package using pip:

```bash
pip install git_llm_troubleshoot
```

## Usage

Here is an example of how to use the `git_llm_troubleshoot` function:

```python
from git_llm_troubleshoot import git_llm_troubleshoot

# Example usage with default LLM
response = git_llm_troubleshoot(user_input="I accidentally deleted my branch.")
print(response)
```

### Input Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default `ChatLLM7` will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the `LLM7_API_KEY` environment variable will be used.

### Custom LLM Integration

You can use other LLMs by passing your own LLM instance to the `git_llm_troubleshoot` function.

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from git_llm_troubleshoot import git_llm_troubleshoot

llm = ChatOpenAI()
response = git_llm_troubleshoot(user_input="I accidentally deleted my branch.", llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from git_llm_troubleshoot import git_llm_troubleshoot

llm = ChatAnthropic()
response = git_llm_troubleshoot(user_input="I accidentally deleted my branch.", llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from git_llm_troubleshoot import git_llm_troubleshoot

llm = ChatGoogleGenerativeAI()
response = git_llm_troubleshoot(user_input="I accidentally deleted my branch.", llm=llm)
print(response)
```

## LLM7 API Key and Rate Limits

By default, the package uses `ChatLLM7` from `langchain_llm7` with its default free tier rate limits, which are generally sufficient for most use cases. If you require higher rate limits for `ChatLLM7`, you can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/). You can then provide this API key either by setting the `LLM7_API_KEY` environment variable or by passing it directly to the `git_llm_troubleshoot` function using the `api_key` parameter.

## Contributing

Please report any issues or feature requests on the GitHub issues page: [https://github.com/chigwell/git-llm-troubleshoot/issues](https://github.com/chigwell/git-llm-troubleshoot/issues).

## Author

- **Eugene Evstafev** - [hi@eugene.plus](mailto:hi@eugene.plus)
- **GitHub Nickname:** chigwell

## License

This project is licensed under the MIT License.