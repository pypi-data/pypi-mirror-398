# termdeployr-llm7
[![PyPI version](https://badge.fury.io/py/termdeployr-llmdeploy-stepdeploy-cliassist-deployflow-termguide-llmdeployer-deploymate-terminaldeploy-smartdeploy.svg)](https://badge.fury.io/py/termdeployr-llmdeploy-stepdeploy-cliassist-deployflow-termguide-llmdeployer-deploymate-terminaldeploy-smartdeploy)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/termdeployr-llmdeploy-stepdeploy-cliassist-deployflow-termguide-llmdeployer-deploymate-terminaldeploy-smartdeploy)](https://pepy.tech/project/termdeployr-llmdeploy-stepdeploy-cliassist-deployflow-termguide-llmdeployer-deploymate-terminaldeploy-smartdeploy)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


## Overview

**termdeployr-llm7** is a lightweight Python package that helps developers deploy applications directly from the terminal.  
It guides you step‑by‑step with clear, actionable terminal commands, parsing your deployment goals or issues and returning structured responses that match a strict regex pattern.  

The core of the package uses **LLM7** via the `ChatLLM7` class from the `langchain_llm7` integration, but you can plug in any other LangChain‑compatible LLM if you prefer.

## Installation

```bash
pip install termdeployr-llm7
```

## Quick Start

```python
from termdeployr_llm7 import termdeployr_llm7

# Minimal call – uses default ChatLLM7 and the LLM7_API_KEY env variable
response = termdeployr_llm7(
    user_input="I want to deploy a Django app to AWS Elastic Beanstalk"
)

print(response)  # => list of terminal commands / instructions
```

## Function Signature

```python
def termdeployr_llm7(
    user_input: str,
    api_key: Optional[str] = None,
    llm: Optional[BaseChatModel] = None,
) -> List[str]:
    """
    Returns a list of terminal commands that fulfill the deployment request.
    
    Parameters
    ----------
    user_input : str
        The natural‑language description of the deployment goal or problem.
    api_key : Optional[str]
        LLM7 API key. If omitted, the function looks for the `LLM7_API_KEY`
        environment variable, falling back to a placeholder key.
    llm : Optional[BaseChatModel]
        Any LangChain `BaseChatModel` instance. If not provided, the default
        `ChatLLM7` client is instantiated.
    """
```

## Using a Custom LLM

You can safely replace the default `ChatLLM7` with any LangChain‑compatible chat model.

### OpenAI

```python
from langchain_openai import ChatOpenAI
from termdeployr_llm7 import termdeployr_llm7

llm = ChatOpenAI(model="gpt-4o-mini")
response = termdeployr_llm7(
    user_input="Deploy a Flask app to Railway",
    llm=llm
)
```

### Anthropic

```python
from langchain_anthropic import ChatAnthropic
from termdeployr_llm7 import termdeployr_llm7

llm = ChatAnthropic(model="claude-3-opus-20240229")
response = termdeployr_llm7(
    user_input="Set up CI/CD for a Node.js project on GitHub Actions",
    llm=llm
)
```

### Google Generative AI

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from termdeployr_llm7 import termdeployr_llm7

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
response = termdeployr_llm7(
    user_input="Create Docker images for a Go microservice",
    llm=llm
)
```

## API Key & Rate Limits

- The **free tier** of LLM7 provides sufficient rate limits for typical deployment assistance.
- To obtain a free API key, register at: <https://token.llm7.io/>
- You can set the key via the environment variable `LLM7_API_KEY` or pass it directly:

```python
response = termdeployr_llm7(
    user_input="Deploy a static site to Netlify",
    api_key="sk_XXXXXXXXXXXXXXXX"
)
```

If higher usage limits are required, upgrade your LLM7 plan and use the new key.

## Contributing

Issues, bug reports, and feature requests are welcomed. Please open a new issue on GitHub:

```
https://github.com/chigwell/termdeployr-llm7/issues
```

## Author

**Eugene Evstafev** – [hi@euegne.plus](mailto:hi@euegne.plus)  
GitHub: [chigwell](https://github.com/chigwell)

---

Happy deploying! 🚀