# TextNoise Analyzer
[![PyPI version](https://badge.fury.io/py/textnoise-analyzer.svg)](https://badge.fury.io/py/textnoise-analyzer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/textnoise-analyzer)](https://pepy.tech/project/textnoise-analyzer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


TextNoise Analyzer is a Python package that helps users determine the noise level of their environment by analyzing text descriptions. Users input a brief text describing their surroundings, and the package processes this input to classify the noise level as low, moderate, or high. The structured output provides a clear assessment of the noise level, enabling applications like smart home systems, workplace environment monitoring, or personal safety tools to respond based on user-provided descriptions.

## Features

- Analyze text descriptions to classify noise levels.
- Supports custom language models (LLMs) from LangChain.
- Defaults to using ChatLLM7 from LangChain LLM7.
- Easy integration with popular LLMs like OpenAI, Anthropic, and Google Generative AI.

## Installation

You can install the package using pip:

```bash
pip install textnoise_analyzer
```

## Usage

### Basic Example

```python
from textnoise_analyzer import textnoise_analyzer

user_input = "I can hear the sound of traffic and people talking."
response = textnoise_analyzer(user_input)
print(response)
```

### Using a Custom LLM

You can use a custom LLM from LangChain by passing it to the `textnoise_analyzer` function.

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from textnoise_analyzer import textnoise_analyzer

llm = ChatOpenAI()
user_input = "I can hear the sound of traffic and people talking."
response = textnoise_analyzer(user_input, llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from textnoise_analyzer import textnoise_analyzer

llm = ChatAnthropic()
user_input = "I can hear the sound of traffic and people talking."
response = textnoise_analyzer(user_input, llm=llm)
print(response)
```

#### Using Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from textnoise_analyzer import textnoise_analyzer

llm = ChatGoogleGenerativeAI()
user_input = "I can hear the sound of traffic and people talking."
response = textnoise_analyzer(user_input, llm=llm)
print(response)
```

### Parameters

- `user_input` (str): The user input text to process.
- `llm` (Optional[BaseChatModel]): The LangChain LLM instance to use. If not provided, the default ChatLLM7 will be used.
- `api_key` (Optional[str]): The API key for LLM7. If not provided, the environment variable `LLM7_API_KEY` will be used.

## Rate Limits

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own API key via the `api_key` parameter or set the environment variable `LLM7_API_KEY`.

You can get a free API key by registering at [LLM7 Token](https://token.llm7.io/).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/textnoise-analyzer).

## License

This project is licensed under the MIT License.

## Author

- **Eugene Evstafev**
- Email: [hi@euegne.plus](mailto:hi@euegne.plus)
- GitHub: [chigwell](https://github.com/chigwell)