# undesirablereasons
[![PyPI version](https://badge.fury.io/py/undesirablereasons.svg)](https://badge.fury.io/py/undesirablereasons)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/undesirablereasons)](https://pepy.tech/project/undesirablereasons)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


`undesirablereasons` is a lightweight Python package that helps you extract and organize key “undesirable” reasons from free‑form text. It leverages **llmatch‑messages** together with a language model (by default **ChatLLM7**) to return a clean, structured list of reasons – perfect for content creators, researchers, or anyone who wants to summarize the negative aspects of a topic.

## Installation

```bash
pip install undesirablereasons
```

## Quick Start

```python
from undesirablereasons import undesirablereasons

user_input = """
Becoming famous sounds great, but it also means losing privacy,
being constantly judged, dealing with paparazzi, and facing intense
pressure to maintain a public image. Fame can attract false
friendships, tax complexities, and the loss of a normal childhood.
"""

reasons = undesirablereasons(user_input)
print(reasons)
```

**Output (example)**

```python
[
    "Loss of privacy",
    "Constant judgment and pressure",
    "Paparazzi intrusion",
    "False friendships",
    "Tax complexities",
    "Loss of a normal childhood"
]
```

## API Reference

### `undesirablereasons(user_input, api_key=None, llm=None) -> List[str]`

| Parameter | Type | Description |
|-----------|------|-------------|
| **user_input** | `str` | The raw text you want to analyse. |
| **api_key** | `Optional[str]` | API key for LLM7. If omitted, the function reads `LLM7_API_KEY` from the environment or falls back to the default (free tier). |
| **llm** | `Optional[BaseChatModel]` | Any LangChain `BaseChatModel` instance. If omitted, the package creates a `ChatLLM7` instance automatically. |

- Returns a list of extracted reasons (strings).  
- Raises `RuntimeError` if the LLM call fails.

## Using a Custom LLM

You can plug in any LangChain‑compatible chat model:

### OpenAI

```python
from langchain_openai import ChatOpenAI
from undesirablereasons import undesirablereasons

llm = ChatOpenAI(model="gpt-4o-mini")
reasons = undesirablereasons("...", llm=llm)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from undesirablereasons import undesirablereasons

llm = ChatAnthropic(model="claude-3-haiku-20240307")
reasons = undesirablereasons("...", llm=llm)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from undesirablereasons import undesirablereasons

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
reasons = undesirablereasons("...", llm=llm)
```

## LLM7 Rate Limits

The free tier of LLM7 provides generous rate limits that are sufficient for most typical uses of this package. If you need higher limits, simply provide your own API key:

```python
reasons = undesirablereasons("...", api_key="YOUR_LLM7_API_KEY")
```

You can obtain a free API key by registering at **https://token.llm7.io/**.

## Development

- **Repository:** https://github.com/chigwell/undesirablereasons  
- **Issues:** https://github.com/chigwell/undesirablereasons/issues  

Feel free to open an issue for bugs, feature requests, or questions.

## Contributing

Contributions are welcome! Fork the repository, make your changes, and submit a pull request. Please ensure that new code follows the existing style and includes appropriate tests.

## License

This project is licensed under the MIT License.

## Author

**Eugene Evstafev** – [hi@euegne.plus](mailto:hi@euegne.plus)  

GitHub: [chigwell](https://github.com/chigwell)