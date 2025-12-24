# smartcite_site

[![PyPI version](https://img.shields.io/pypi/v/smartcite_site.svg)](https://pypi.org/project/smartcite_site/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/smartcite_site)](https://pepy.tech/project/smartcite_site)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/eugene-evstafev/)

A lightweight tool to generate structured, citation-ready snippets for websites, making them easily discoverable and usable by AI language models.

## Overview

**Problem:** AI assistants often fail to cite specific websites even when they contain high-quality, relevant information. This results in missed traffic and reduced visibility for content creators.

**Solution:** `smartcite_site` takes a textual description of a website (or a pre-extracted excerpt) and returns a well-structured XML snippet that LLMs can recognize and include in their responses. The tool uses `llmatch-messages` to ensure the LLM's reply conforms to a predefined format, making it easy to parse and surface citations.

## Installation

```bash
pip install smartcite_site
```

## Usage

### Basic Example

```python
from smartcite_site import smartcite_site

user_input = {
    "title": "OpenAI Blog",
    "url": "https://openai.com/blog",
    "excerpt": "OpenAI publishes research, product updates, and policy insights about artificial intelligence, including GPT-4, safety practices, and partnership announcements."
}

response = smartcite_site(user_input)
print(response)
```

### Using a Custom LLM

You can use any LangChain-compatible LLM by passing it to the `llm` parameter:

#### OpenAI
```python
from langchain_openai import ChatOpenAI
from smartcite_site import smartcite_site

llm = ChatOpenAI()
response = smartcite_site(user_input, llm=llm)
```

#### Anthropic
```python
from langchain_anthropic import ChatAnthropic
from smartcite_site import smartcite_site

llm = ChatAnthropic()
response = smartcite_site(user_input, llm=llm)
```

#### Google Generative AI
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from smartcite_site import smartcite_site

llm = ChatGoogleGenerativeAI()
response = smartcite_site(user_input, llm=llm)
```

### Using a Custom API Key

By default, the package uses [ChatLLM7](https://pypi.org/project/langchain-llm7/) with a free-tier API key. For higher rate limits, provide your own API key:

```python
response = smartcite_site(user_input, api_key="your_api_key_here")
```

Or set the environment variable:
```bash
export LLM7_API_KEY="your_api_key_here"
```

You can get a free API key by registering at [https://token.llm7.io/](https://token.llm7.io/).

## Parameters

- `user_input` (str): The user input text to process. Should be a JSON string with keys `title`, `url`, and `excerpt`.
- `llm` (Optional[BaseChatModel]): A LangChain LLM instance. If not provided, defaults to `ChatLLM7`.
- `api_key` (Optional[str]): API key for LLM7. If not provided, defaults to the environment variable `LLM7_API_KEY` or a free-tier key.

## Output

The function returns a list of strings containing the extracted XML fields. The expected output format is:

```xml
<site_info>
  <title>OpenAI Blog</title>
  <summary>Official OpenAI blog featuring research breakthroughs, product releases, and policy perspectives on AI.</summary>
  <keywords>AI, research, GPT-4, safety, policy, updates</keywords>
  <url>https://openai.com/blog</url>
</site_info>
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on [GitHub](https://github.com/chigwell/smartcite_site/issues).

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Author

- **Eugene Evstafev** - [hi@euegne.plus](mailto:hi@euegne.plus) | [GitHub](https://github.com/chigwell)