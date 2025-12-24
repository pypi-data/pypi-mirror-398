# image-text-structurizer
[![PyPI version](https://badge.fury.io/py/image-text-structurizer.svg)](https://badge.fury.io/py/image-text-structurizer)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/image-text-structurizer)](https://pepy.tech/project/image-text-structurizer)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package to process user-provided text descriptions of images and extract structured, validated outputs using pattern matching and a language model. Ensures that the output adheres to a predefined format such as XML-like tags, facilitating consistent and reliable extraction of image metadata or summaries without directly handling image data.

## Installation

Install via pip:

```bash
pip install image_text_structurizer
```

## Usage Example

```python
from image_text_structurizer import image_text_structurizer

response = image_text_structurizer(user_input="A scenic landscape with mountains and a river")
print(response)
```

## Function Parameters

- `user_input` (str): The text description of the image to process.
- `llm` (Optional[BaseChatModel]): An instance of a language model. Defaults to `ChatLLM7` from `langchain_llm7`.
- `api_key` (Optional[str]): API key for accessing the `ChatLLM7` model. If not provided, it attempts to fetch from environment variable `LLM7_API_KEY`. You can also set it directly in code.

## Supported Language Models

This package uses `ChatLLM7` by default, which can be imported from `langchain_llm7`. Developers can pass other models, such as:

- OpenAI Chat models
- Anthropic models
- Google Generative AI models

by creating an instance and passing it to the `image_text_structurizer` function.

### Examples:

Using OpenAI:

```python
from langchain_openai import ChatOpenAI
from image_text_structurizer import image_text_structurizer

llm = ChatOpenAI()
response = image_text_structurizer(user_input="A sunset over the ocean", llm=llm)
```

Using Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from image_text_structurizer import image_text_structurizer

llm = ChatAnthropic()
response = image_text_structurizer(user_input="A forest with tall trees and fog", llm=llm)
```

Using Google Generative AI:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from image_text_structurizer import image_text_structurizer

llm = ChatGoogleGenerativeAI()
response = image_text_structurizer(user_input="A city skyline at night", llm=llm)
```

## Notes
- The package relies on the `ChatLLM7` model from `langchain_llm7`. 
- Default rate limits are suitable for most use cases, but higher limits can be obtained by registering for an API key at [https://token.llm7.io/](https://token.llm7.io/).
- To pass your own API key, set the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = image_text_structurizer(user_input="Example text", api_key="your_api_key")
```

## Support & Contributions

- For issues, open an issue on the [GitHub repository](https://github.com/...). 

## Author

- **Eugene Evstafev**  
  Email: [hi@eugene.plus](mailto:hi@eugene.plus)  
  GitHub: [https://github.com/chigwell](https://github.com/chigwell)