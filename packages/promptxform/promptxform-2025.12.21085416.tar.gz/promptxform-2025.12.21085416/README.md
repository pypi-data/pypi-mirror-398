# promptxform
[![PyPI version](https://badge.fury.io/py/promptxform.svg)](https://badge.fury.io/py/promptxform)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/promptxform)](https://pepy.tech/project/promptxform)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

A simple and efficient way to process user input text with ChatLLM7

**Overview**

promptxform is a Python package designed to simplify user interactions by accepting free-text prompts and providing structured, reliable responses. It leverages an underlying pattern-matching system to interpret user inputs and generate consistent outputs, enabling seamless information extraction or task execution without complex processing of media types.

**Installation**
```bash
pip install promptxform
```
**Example usage**
```python
from promptxform import promptxform

response = promptxform(user_input="my text here")
```
**Input parameters**

* `user_input`: str - the user input text to process
* `llm`: Optional[BaseChatModel] - the langchain llm instance to use, if not provided the default ChatLLM7 will be used.
* `api_key`: Optional[str] - the api key for llm7, if not provided it will use the default ChatLLM7 from langchain_llm7.

**Using your own LLM instance**

You can safely pass your own llm instance (based on [langchain documentation](https://docs.langchain.readthedocs.io/en/latest/)) if you want to use another LLM, via passing it like `promptxform(user_input, llm=your_llm_instance)`.

Here are some examples:

```python
from langchain_openai import ChatOpenAI
from promptxform import promptxform
llm = ChatOpenAI()
response = promptxform(user_input, llm=llm)

from langchain_anthropic import ChatAnthropic
from promptxform import promptxform
llm = ChatAnthropic()
response = promptxform(user_input, llm=llm)

from langchain_google_genai import ChatGoogleGenerativeAI
from promptxform import promptxform
llm = ChatGoogleGenerativeAI()
response = promptxform(user_input, llm=llm)
```

**Rate limits**

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7 you can pass your api key via environment variable LLM7_API_KEY or via passing it directly like `promptxform(user_input, api_key="your_api_key")`. You can get a free api key by registering at https://token.llm7.io/

**Support and issues**

Please report any issues you encounter at [github issues page](https://github.com/chigwell/promptxform/issues)

**Author**

Eugene Evstafev (eugene@eugene.plus)
Alenaova Systems