# clima-nutri
[![PyPI version](https://badge.fury.io/py/clima-nutri.svg)](https://badge.fury.io/py/clima-nutri)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/clima-nutri)](https://pepy.tech/project/clima-nutri)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


clima-nutri is a Python package designed to assist researchers, policymakers, and health professionals in understanding the impact of rising carbon dioxide levels on food quality. This tool analyzes text input describing food-related studies, reports, or observations and extracts structured summaries highlighting key findings about increasing caloric contents and decreasing nutritional values of food due to climate change. Leveraging advanced language models and pattern matching, clima-nutri simplifies the process of trend analysis, data comparison, and strategy development to mitigate adverse climate effects on nutrition.

## Installation

Install the package via pip:

```bash
pip install clima_nutri
```

## Usage

Import the package and call the main function with your input text. You can use the default language model (ChatLLM7 from langchain_llm7), or pass a custom instance of any compatible language model.

### Basic example with default LLM:

```python
from clima_nutri import clima_nutri

response = clima_nutri(user_input="Your text describing studies or observations about food and climate change.")
print(response)
```

### Using your own language model instance

The package defaults to using `ChatLLM7` from `langchain_llm7` sourced from PyPI (https://pypi.org/project/langchain-llm7/). You can also provide your own LLM instance for flexibility, such as OpenAI, Anthropic, or Google models.

#### Example with OpenAI:

```python
from langchain_openai import ChatOpenAI
from clima_nutri import clima_nutri

llm = ChatOpenAI()
response = clima_nutri(user_input="Your input text here.", llm=llm)
```

#### Example with Anthropic:

```python
from langchain_anthropic import ChatAnthropic
from clima_nutri import clima_nutri

llm = ChatAnthropic()
response = clima_nutri(user_input="Your input text here.", llm=llm)
```

#### Example with Google Generative AI:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from clima_nutri import clima_nutri

llm = ChatGoogleGenerativeAI()
response = clima_nutri(user_input="Your input text here.", llm=llm)
```

### API Key Management

The function can automatically retrieve the default API key for LLM7 from the environment variable `LLM7_API_KEY`. For higher rate limits or custom usage, you can pass your API key directly:

```python
response = clima_nutri(user_input="Your input text here.", api_key="your_api_key")
```

You can obtain a free API key at [https://token.llm7.io/](https://token.llm7.io/).

## Function Signature

```python
clima_nutri(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None
) -> List[str]
```

- **user_input**: Text describing food studies, reports, or observations.
- **api_key**: Optional string for LLM7 API access.
- **llm**: Optional custom language model instance; defaults to `ChatLLM7`.

## Underlying Technology

This package relies on `ChatLLM7` from the `langchain_llm7` library. It enables flexible integration with various language models, including OpenAI, Anthropic, and Google Generative AI, facilitating broad compatibility.

## Support and Feedback

For issues or feature requests, please visit the GitHub repository: [https://github.com/chigwell/clima-nutri/issues](https://github.com/chigwell/clima-nutri/issues)

## Author

Eugene Evstafev  
Email: hi@euegne.plus  
GitHub: [@chigwell](https://github.com/chigwell)