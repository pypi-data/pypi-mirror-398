# Tech-Discriptor
[![PyPI version](https://badge.fury.io/py/tech-discriptor.svg)](https://badge.fury.io/py/tech-discriptor)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/tech-discriptor)](https://pepy.tech/project/tech-discriptor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

Transform technical descriptions into structured summaries and feature lists

## Overview
A new package designed to transform technical descriptions of hardware or software solutions into structured summaries and feature lists.

## Installation
```bash
pip install tech_discriptor
```
## Example Usage
```python
from tech_discriptor import tech_discriptor

user_input = "Romforth—an ultra-portable, small, bare-metal Forth implementation for multiple processors—"
response = tech_discriptor(user_input)

print(response)
```
## Input Parameters
* `user_input`: `str` - the user input text to process
* `llm`: `Optional[BaseChatModel]` - the langchain llm instance to use, if not provided the default ChatLLM7 will be used.
* `api_key`: `Optional[str]` - the api key for llm7, if not provided the default ChatLLM7 will be used.

## Supported LLMs
You can safely pass your own llm instance (based on <https://docs.langchain.io/docs/guides/get-started-with-a-model>) if you want to use another LLM, via passing it like `tech_discriptor(user_input, llm=their_llm_instance)`.

### Examples
#### OpenAI
```python
from langchain_openai import ChatOpenAI
from tech_discriptor import tech_discriptor

llm = ChatOpenAI()
response = tech_discriptor(user_input, llm=llm)
```
#### Anthropic
```python
from langchain_anthropic import ChatAnthropic
from tech_discriptor import tech_discriptor

llm = ChatAnthropic()
response = tech_discriptor(user_input, llm=llm)
```
#### Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from tech_discriptor import tech_discriptor

llm = ChatGoogleGenerativeAI()
response = tech_discriptor(user_input, llm=llm)
```
## API Key for LLM7
The default `ChatLLM7` LLM is used if no custom LLM is provided. The free tier rate limits are generally sufficient. For higher rate limits with `ChatLLM7`, you can:
* Set the `LLM7_API_KEY` environment variable.
* Pass the API key directly: `tech_discriptor(user_input, api_key="your_api_key")`
You can obtain a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/)

## Contributing
Contributions are welcome! Please refer to the GitHub repository for details.

## License
This project is licensed under the [MIT License](LICENSE).

## Author
* Eugene Evstafev (hi@eugene.plus)

## Contact
For issues or questions, please visit the GitHub issues page: [https://github.com/chigwell/tech-discriptor/](https://github.com/chigwell/tech-discriptor/)