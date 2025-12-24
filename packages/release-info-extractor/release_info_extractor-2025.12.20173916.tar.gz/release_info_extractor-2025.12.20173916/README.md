# Release Info Extractor

[![PyPI version](https://badge.fury.io/py/release-info-extractor.svg)](https://pypi.org/project/release-info-extractor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/personalized-badge/release-info-extractor?period=total&units=international_system&left_color=grey&right_color=orange&left_text=Downloads)](https://pepy.tech/project/release-info-extractor)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/eugene-evstafev/)

A Python package that transforms free-form software release announcements into a concise, machine-readable summary.

## Overview

This package extracts key attributes such as version number, new features, architectural changes, and compatibility notes from raw textual descriptions of software releases. The extracted information is returned in a structured format (e.g., JSON or XML), enabling downstream tools to consume the information reliably without manual parsing.

## Installation

```bash
pip install release-info-extractor
```

## Usage

### Basic Usage

```python
from release_info_extractor import release_info_extractor

response = release_info_extractor("GDB 17.1 Released with shadow and guard stack support")
print(response)
```

### Using a Custom LLM

By default, the package uses `ChatLLM7` from `langchain_llm7`. However, you can pass your own LLM instance if you want to use another LLM.

#### Using OpenAI

```python
from langchain_openai import ChatOpenAI
from release_info_extractor import release_info_extractor

llm = ChatOpenAI()
response = release_info_extractor("GDB 17.1 Released with shadow and guard stack support", llm=llm)
print(response)
```

#### Using Anthropic

```python
from langchain_anthropic import ChatAnthropic
from release_info_extractor import release_info_extractor

llm = ChatAnthropic()
response = release_info_extractor("GDB 17.1 Released with shadow and guard stack support", llm=llm)
print(response)
```

#### Using Google

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from release_info_extractor import release_info_extractor

llm = ChatGoogleGenerativeAI()
response = release_info_extractor("GDB 17.1 Released with shadow and guard stack support", llm=llm)
print(response)
```

### Using a Custom API Key

The default rate limits for LLM7 free tier are sufficient for most use cases. If you need higher rate limits, you can pass your own API key via an environment variable or directly in the function call.

#### Using Environment Variable

```bash
export LLM7_API_KEY="your_api_key"
```

#### Directly in Function Call

```python
from release_info_extractor import release_info_extractor

response = release_info_extractor("GDB 17.1 Released with shadow and guard stack support", api_key="your_api_key")
print(response)
```

You can get a free API key by registering at [LLM7](https://token.llm7.io/).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Eugene Evstafev**

- **Email:** hi@eugene.plus
- **LinkedIn:** [Eugene Evstafev](https://www.linkedin.com/in/eugene-evstafev/)

## Issues

If you encounter any issues or have suggestions, please open an issue on [GitHub](https://github.com/yourusername/release-info-extractor/issues).