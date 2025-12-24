# nlboard
[![PyPI version](https://badge.fury.io/py/nlboard.svg)](https://badge.fury.io/py/nlboard)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/nlboard)](https://pepy.tech/project/nlboard)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


nlboard is a Python package designed to transform unstructured user input about project management needs into a structured Trello-like board configuration. By leveraging large language models, nlboard interprets plain text descriptions of tasks, workflows, and preferences and outputs a well-organized Trello board setting with lists, cards, and labels. This enables users to quickly set up a modern project management interface tailored to their specific requirements without manual configuration.

## Installation

Install via pip:

```bash
pip install nlboard
```

## Usage

Here's a basic example of how to use nlboard with the default LLM:

```python
from nlboard import nlboard

user_input = "I need a board for managing my software project with to-do, in-progress, and done lists. Add cards for feature development, bug fixes, and documentation. Use labels for priority levels."

response = nlboard(user_input)
print(response)
```

## Custom LLM Support

nlboard defaults to using the `ChatLLM7` from `langchain_llm7`, but you can pass your own language model instance to customize the setup.

### Using different language models

You can easily pass your preferred LLM, such as OpenAI, Anthropic, or Google Generative AI, as shown below:

```python
from langchain_openai import ChatOpenAI
from nlboard import nlboard

llm = ChatOpenAI()
response = nlboard(user_input, llm=llm)
```

Similarly, for other LLMs:

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic()
response = nlboard(user_input, llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI()
response = nlboard(user_input, llm=llm)
```

### API Key Configuration

The default use of LLM7 is suitable for most cases, especially with its free tier. To improve rate limits, set your API key:

- Via environment variable:

```bash
export LLM7_API_KEY='your-api-key'
```

- Or pass directly in code:

```python
response = nlboard(user_input, api_key='your-api-key')
```

You can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Notes

- The package relies on `langchain_llm7` (https://pypi.org/project/langchain-llm7/).
- You can easily integrate other language models by passing customized `BaseChatModel` instances.

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)

## Issues

For bugs or feature requests, create an issue on the [GitHub repository](https://github.com/chigwell/nlboard/issues).