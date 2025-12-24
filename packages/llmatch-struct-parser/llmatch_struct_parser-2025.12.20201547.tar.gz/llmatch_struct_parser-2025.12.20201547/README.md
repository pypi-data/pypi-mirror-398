# LLMatch Struct Parser Package

LLMatch Struct Parser is a Python package designed to enhance structured text processing by leveraging the capabilities of llmatch-messages. It takes user-provided text as input and returns a well-organized, structured response using the power of llm7 and llmatch.

## Overview

This package is particularly useful for applications that require reliable and structured data extraction from textual inputs, avoiding complex media processing like documents, audio, video, or URLs. It streamlines the process of obtaining structured data, making it easier to integrate into various applications and workflows.

## Installation

```bash
pip install llmatch_struct_parser
```

## Usage

```python
from llmatch_struct_parser import llmatch_struct_parser

def process_text(user_input: str) -> List[str]:
    response = llmatch_struct_parser(
        user_input=user_input,
        api_key="your_api_key",
        llm="your_llm_instance"
    )
    return response

# Recommended usage
api_key = os.environ.get("LLM7_API_KEY")
llm = ChatLLM7(api_key=api_key)

response = llmatch_struct_parser(
    user_input="your_input_text",
    api_key=api_key,
    llm=llm
)

print(response)
```

## Parameters

- `user_input`: the user input text to process
- `llm`: the langchain llm instance to use, if not provided the default ChatLLM7 will be used
- `api_key`: the api key for llm7, if not provided the default llm7 api key will be used

## Using Custom LLM Instances

```python
from langchain_openai import ChatOpenAI
from llmatch_struct_parser import llmatch_struct_parser

llm = ChatOpenAI()
response = llmatch_struct_parser(user_input="your_input_text", llm=llm)
```

```python
from langchain_anthropic import ChatAnthropic
from llmatch_struct_parser import llmatch_struct_parser

llm = ChatAnthropic()
response = llmatch_struct_parser(user_input="your_input_text", llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from llmatch_struct_parser import llmatch_struct_parser

llm = ChatGoogleGenerativeAI()
response = llmatch_struct_parser(user_input="your_input_text", llm=llm)
```

## Rate Limiting

The default rate limits for LLM7 free tier are sufficient for most use cases of this package. If you need higher rate limits, you can pass your own api_key via environment variable LLM7_API_KEY or via passing it directly like `llmatch_struct_parser(api_key="your_api_key")`.

## Getting Started

Get your free LLM7 api key by registering at <https://token.llm7.io/>.

## Support and Issues

Visit <https://github.com/chigwell/llmatch-struct-parser> for support and issue reporting.

## License

This package is licensed under the MIT License.

## Author

Eugene Evstafev, <hi@euegne.plus>

## GitHub

[chigwell](https://github.com/chigwell)

[![PyPI version](https://badge.fury.io/py/llmatch-struct-parser.svg)](https://badge.fury.io/py/llmatch-struct-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/llmatch-struct-parser.svg)](https://pypi.org/project/llmatch-struct-parser/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Eugene_Evstafev-blue)](https://www.linkedin.com/in/eugene-evstafev/)