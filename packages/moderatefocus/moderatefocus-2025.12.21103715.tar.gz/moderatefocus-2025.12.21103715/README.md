# ModerateFocus
[![PyPI version](https://badge.fury.io/py/moderatefocus.svg)](https://badge.fury.io/py/moderatefocus)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/moderatefocus)](https://pepy.tech/project/moderatefocus)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)

### Analyzing Community Moderation and Platform Policies

**Overview**
ModerateFocus is a Python package that helps analyze user-submitted text queries about community moderation or platform policies. It uses a Large Language Model (LLM) to generate reasoned explanations and extract key points using pattern matching. This ensures consistent, non-opinionated output, helping users understand common moderation pitfalls without delving into sensitive or subjective areas.

**Installation**
```bash
pip install moderatefocus
```
**Usage**
```python
from moderatefocus import moderatefocus

response = moderatefocus(user_input, api_key="your_api_key_here")
print(response)  # Output: list of extracted key points
```
**Parameters**
- `user_input`: str - the user input text to process
- `api_key`: Optional[str] - the API key for LLM7, if not provided, the default ChatLLM7 will be used
- `llm`: Optional[BaseChatModel] - the langchain LLM instance to use, if not provided, the default ChatLLM7 will be used

**Using Custom LLM Instances**
You can safely pass your own LLM instance (based on [langchain](https://docs.langchain.com) if you want to use another LLM. For example:
```python
from langchain_openai import ChatOpenAI
from moderatefocus import moderatefocus

llm = ChatOpenAI()
response = moderatefocus(user_input, llm=llm)
```

**Using Another LLM**
You can use another LLM like anthropic or google. For example:
```python
from langchain_anthropic import ChatAnthropic
from moderatefocus import moderatefocus

llm = ChatAnthropic()
response = moderatefocus(user_input, llm=llm)
```
or google:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from moderatefocus import moderatefocus

llm = ChatGoogleGenerativeAI()
response = moderatefocus(user_input, llm=llm)
```
**API Key Rate Limits**
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits for LLM7, you can pass your own API key via environment variable LLM7_API_KEY or via passing it directly like `moderatefocus(user_input, api_key="your_api_key_here")`. You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

**Author**
Eugene Evstafev ([hi@eugene.plus](mailto:hi@eugene.plus))

**GitHub**
[https://github.com/chigwell](https://github.com/chigwell)

**License**
[MIT License](https://opensource.org/licenses/MIT)