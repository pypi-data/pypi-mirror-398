# PartnershipParser
[![PyPI version](https://badge.fury.io/py/partnershipparser.svg)](https://badge.fury.io/py/partnershipparser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/partnershipparser)](https://pepy.tech/project/partnershipparser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


PartnershipParser is a Python package designed to extract and structure key information from news articles or press releases about strategic partnerships in the technology sector. It processes unstructured text inputs to produce a standardized output that includes the collaborating companies, the focus area of their collaboration, and the potential impact or goals mentioned. This facilitates quick analysis and comparison of multiple partnership announcements, helping business analysts, investors, and researchers identify industry trends, competitive advantages, and market opportunities.

## Features

- Extracts key partnership details from free-text sources
- Outputs structured, consistent data for easier downstream analysis
- Utilizes advanced language models with flexible options
- Easy to integrate into larger data processing pipelines

## Installation

Install PartnershipParser via pip:

```bash
pip install partnershipparser
```

## Usage

Below is an example of how to use the package in your Python code:

```python
from partnershipparser import partnershipparser

user_input = "Apple and Google announced a collaboration to develop sustainable AI chips."
response = partnershipparser(user_input)
print(response)
```

### Parameters:

- `user_input` (str): The text content of the article or press release to analyze.
- `llm` (Optional[BaseChatModel]): An instance of a language model to use for processing. Defaults to `ChatLLM7` from `langchain_llm7`.
- `api_key` (Optional[str]): API key for `ChatLLM7`. If not provided, it will attempt to read from environment variable `LLM7_API_KEY`. You can also pass it directly.

## Supported Language Models

The package defaults to `ChatLLM7` from `langchain_llm7` ( https://pypi.org/project/langchain-llm7/ ). Users can pass custom language model instances such as:

```python
from langchain_openai import ChatOpenAI
from partnershipparser import partnershipparser

llm = ChatOpenAI()
response = partnershipparser(user_input, llm=llm)
```

You can also use other supported models by importing and instantiating them similarly, such as `ChatAnthropic`, `ChatGoogleGenerativeAI`, etc. Refer to their respective documentation for setup.

## Rate Limits and API Keys

The default rate limits for LLM7's free tier are suitable for most uses of this package. To obtain higher limits, you can:

- Set `LLM7_API_KEY` environment variable
- Pass your API key directly in `partnershipparser()`:

```python
response = partnershipparser(user_input, api_key="your_api_key")
```

Register for a free API key at https://token.llm7.io/

## Contributing

Contributions are welcome! Please open issues or pull requests on our GitHub repository.

## License

This project is licensed under the MIT License.

## Contact

Author: Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [chigwell](https://github.com/chigwell)  
Issues: [https://github.com/yourrepo/partnershipparser/issues](https://github.com/yourrepo/partnershipparser/issues)