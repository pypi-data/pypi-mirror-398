# Game Concept Analyzer
[![PyPI version](https://badge.fury.io/py/gameconcept-analyzer.svg)](https://badge.fury.io/py/gameconcept-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/gameconcept-analyzer)](https://pepy.tech/project/gameconcept-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


Game Concept Analyzer is a Python package designed to assist game developers and enthusiasts in analyzing and refining local multiplayer party game ideas. By processing user-submitted text descriptions of game mechanics, player interactions, and party dynamics, it provides structured feedback and suggestions to enhance game designs. The tool ensures the output is formatted for easy integration into design documents or brainstorming sessions, streamlining the creative process.

## Installation

You can install the package using pip:

```bash
pip install gameconcept_analyzer
```

## Usage

Here's a basic example of how to use the package:

```python
from gameconcept_analyzer import gameconcept_analyzer

# Example user input describing a game concept
user_input = "A fast-paced party game where players compete in mini-challenges sitting around a table."

# Call the analyzer function
response = gameconcept_analyzer(user_input)

# Print the feedback or suggestions
print(response)
```

## Customizing the Language Model

The package uses the `ChatLLM7` from `langchain_llm7` by default, which you can configure or replace to suit your preferences. You can pass your own LLM instance to the `gameconcept_analyzer` function, such as models from OpenAI, Anthropic, or Google.

### Example: Using OpenAI

```python
from langchain_openai import ChatOpenAI
from gameconcept_analyzer import gameconcept_analyzer

llm = ChatOpenAI()
response = gameconcept_analyzer(user_input, llm=llm)
```

### Example: Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from gameconcept_analyzer import gameconcept_analyzer

llm = ChatAnthropic()
response = gameconcept_analyzer(user_input, llm=llm)
```

### Example: Using Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from gameconcept_analyzer import gameconcept_analyzer

llm = ChatGoogleGenerativeAI()
response = gameconcept_analyzer(user_input, llm=llm)
```

### API Key Configuration

For the default `ChatLLM7`, you can provide your API key via the `api_key` parameter or set the environment variable `LLM7_API_KEY`. For higher rate limits, obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/).

```python
response = gameconcept_analyzer(user_input, api_key="your_api_key")
```

## Parameters

- `user_input` (str): The descriptive text of your game concept.
- `llm` (Optional[BaseChatModel]): An instance of a language model compatible with `langchain`. Defaults to `ChatLLM7`.
- `api_key` (Optional[str]): API key for `ChatLLM7`. If not provided, the environment variable or default will be used.

## Support and Issues

If you encounter any problems or have suggestions, please open an issue on the GitHub repository: [https://github.com/chigwell/gameconcept-analyzer](https://github.com/chigwell/gameconcept-analyzer)

## Author

Eugene Evstafev  
Email: hi@eugene.plus  
GitHub: [chigwell](https://github.com/chigwell)