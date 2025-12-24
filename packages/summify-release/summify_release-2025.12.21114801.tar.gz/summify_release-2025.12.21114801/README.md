# summify_release
[![PyPI version](https://badge.fury.io/py/summify-release.svg)](https://badge.fury.io/py/summify-release)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/summify-release)](https://pepy.tech/project/summify-release)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview
A new package that leverages pattern-matched interactions with language models to generate structured summaries of software updates from user-provided text snippets. It focuses on extracting key features, release highlights, and version improvements to deliver concise, organized reports for end-users or documentation purposes, without processing media or external URLs.

## Installation
```bash
pip install summify_release
```

## Usage
```python
from summify_release import summify_release
```

## Input Parameters
- `user_input`: `str`: the user input text to process
- `llm`: `Optional[BaseChatModel]`: the langchain llm instance to use, if not provided the default `ChatLLM7` will be used.
- `api_key`: `Optional[str]`: the api key for llm7, if not provided the default LLM7 api key from the environment variable `LLM7_API_KEY` will be used.

You can safely pass your own `llm` instance (based on https://docs.langchain.com/) if you want to use another LLM, via passing it like `summify_release(user_input, llm=your_llm_instance)`, for example to use the openai https://docs.openai.com/:
```python
from langchain_openai import ChatOpenAI
from summify_release import summify_release
llm = ChatOpenAI()
response = summify_release(user_input, llm=llm)
```
or for example to use the anthropic https://docs.anthropic.tech/:
```python
from langchain_anthropic import ChatAnthropic
from summify_release import summify_release
llm = ChatAnthropic()
response = summify_release(user_input, llm=llm)
```
or google https://docs.google.com/ai-book/docs/:
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from summify_release import summify_release
llm = ChatGoogleGenerativeAI()
response = summify_release(user_input, llm=llm)
```

## LLM7 API Key
The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you want higher rate limits for LLM7 you can pass your own `api_key` via environment variable `LLM7_API_KEY` or via passing it directly like `summify_release(user_input, api_key="your_api_key")`.

You can obtain a free api key by registering at https://token.llm7.io/

## Contributing
Contributions are welcome! Please refer to the issue tracker for details.

## License
This project is licensed under the MIT License.

## Author
* **Eugene Evstafev** - [hi@eugene.plus](mailto:hi@eugene.plus)
* **GitHub:** [chigwell](https://github.com/chigwell)

## GitHub Issues
[https://github.com/chigwell/summify-release/issues](https://github.com/chigwell/summify-release/issues)