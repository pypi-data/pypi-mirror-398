# Drone Capability Parser
[![PyPI version](https://badge.fury.io/py/drone-capability-parser.svg)](https://badge.fury.io/py/drone-capability-parser)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/drone-capability-parser)](https://pepy.tech/project/drone-capability-parser)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


**drone-capability-parser** is a lightweight Python package that extracts structured summaries of a drone’s operational capabilities from free‑form textual descriptions.  
It automatically identifies locomotion methods (e.g., wheeled movement, flight) and unified actuation systems, delivering a clean, standardized output for engineers and designers.

---

## Installation

```bash
pip install drone_capability_parser
```

---

## Quick Start

```python
from drone_capability_parser import drone_capability_parser

# Basic usage – let the library create the default LLM7 client for you
text = """
The new Explorer drone can roll on its six wheeled chassis at up to 15 km/h,
while its rotors enable vertical take‑off and hover for 30 minutes.
All motion is coordinated through a unified actuation controller.
"""
caps = drone_capability_parser(user_input=text)

print(caps)
# -> ['locomotion: wheeled, speed: 15 km/h', 'locomotion: flight, hover_time: 30 min', ...]
```

### Function signature

```python
drone_capability_parser(
    user_input: str,
    llm: Optional[BaseChatModel] = None,
    api_key: Optional[str] = None,
) -> List[str]
```

| Parameter   | Type                             | Description |
|-------------|----------------------------------|-------------|
| `user_input`| `str`                            | The free‑form description of the drone design you want to parse. |
| `llm`       | `Optional[BaseChatModel]`        | A LangChain LLM instance. If omitted, the function creates a `ChatLLM7` client automatically. |
| `api_key`   | `Optional[str]`                  | API key for the LLM7 service. If omitted, the function reads the `LLM7_API_KEY` environment variable, or falls back to a placeholder `"None"` (which triggers the default free‑tier limits). |

---

## Using a Custom LLM

You can plug any LangChain‑compatible chat model that inherits from `BaseChatModel`.  
Below are a few examples:

### OpenAI (`langchain-openai`)

```python
from langchain_openai import ChatOpenAI
from drone_capability_parser import drone_capability_parser

llm = ChatOpenAI(model="gpt-4o-mini")
response = drone_capability_parser(user_input=text, llm=llm)
```

### Anthropic (`langchain-anthropic`)

```python
from langchain_anthropic import ChatAnthropic
from drone_capability_parser import drone_capability_parser

llm = ChatAnthropic(model="claude-3-haiku-20240307")
response = drone_capability_parser(user_input=text, llm=llm)
```

### Google Generative AI (`langchain-google-genai`)

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from drone_capability_parser import drone_capability_parser

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = drone_capability_parser(user_input=text, llm=llm)
```

---

## Default LLM – ChatLLM7

If you do not provide an `llm` instance, **drone_capability_parser** uses `ChatLLM7` from the `langchain_llm7` package:

```text
https://pypi.org/project/langchain-llm7/
```

The free tier of LLM7 offers generous rate limits that satisfy most development and testing scenarios.  
To increase limits, supply a personal API key:

```bash
export LLM7_API_KEY="your_api_key_here"
```

or directly:

```python
response = drone_capability_parser(user_input=text, api_key="your_api_key_here")
```

You can obtain a free API key by registering at:

```
https://token.llm7.io/
```

---

## Contributing & Support

- **Issues:** Please open any bugs or feature requests on the GitHub issue tracker:  
  https://github....
- **Author:** Eugene Evstafev – [hi@euegne.plus](mailto:hi@euegne.plus)  
- **GitHub:** [chigwell](https://github.com/chigwell)

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.