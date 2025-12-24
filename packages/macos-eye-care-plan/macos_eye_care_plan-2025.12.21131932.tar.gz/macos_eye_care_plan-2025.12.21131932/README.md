# macos-eye-care-plan
[![PyPI version](https://badge.fury.io/py/macos-eye-care-plan.svg)](https://badge.fury.io/py/macos-eye-care-plan)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/macos-eye-care-plan)](https://pepy.tech/project/macos-eye-care-plan)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue)](https://www.linkedin.com/in/eugene-evstafev-716669181/)


A Python package that generates personalized 5-day eye care plans for macOS users based on their screen usage patterns and work habits.

## Installation

```bash
pip install macos_eye_care_plan
```

## Usage

```python
from macos_eye_care_plan import macos_eye_care_plan

# Provide information about your screen usage and environment
user_input = """
I work 8-10 hours daily on my MacBook Pro, mostly coding and writing.
My workspace has moderate lighting, and I experience occasional eye strain.
I take short breaks every hour but don't do any specific eye exercises.
"""

# Generate a personalized eye care plan
plan = macos_eye_care_plan(user_input=user_input)

# The plan returns a list of 5 daily schedules
for day, schedule in enumerate(plan, 1):
    print(f"Day {day}: {schedule}")
```

## Parameters

- `user_input` (str): Description of daily screen usage, work environment, and any eye discomfort
- `llm` (Optional[BaseChatModel]): LangChain LLM instance (defaults to ChatLLM7)
- `api_key` (Optional[str]): API key for LLM7 service

## Using Custom LLMs

You can use any LangChain-compatible LLM:

```python
from langchain_openai import ChatOpenAI
from macos_eye_care_plan import macos_eye_care_plan

llm = ChatOpenAI()
response = macos_eye_care_plan(user_input="Your input here", llm=llm)
```

```python
from langchain_anthropic import ChatAnthropic
from macos_eye_care_plan import macos_eye_care_plan

llm = ChatAnthropic()
response = macos_eye_care_plan(user_input="Your input here", llm=llm)
```

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from macos_eye_care_plan import macos_eye_care_plan

llm = ChatGoogleGenerativeAI()
response = macos_eye_care_plan(user_input="Your input here", llm=llm)
```

## LLM7 Configuration

The package uses ChatLLM7 from [langchain_llm7](https://pypi.org/project/langchain-llm7/) by default. For higher rate limits:

```bash
export LLM7_API_KEY="your_api_key"
```

Or pass directly:
```python
response = macos_eye_care_plan(user_input="Your input", api_key="your_api_key")
```

Get a free API key at: https://token.llm7.io/

## Issues

Report issues at: https://github.com/chigwell/macos-eye-care-plan/issues

## Author

Eugene Evstafev (hi@euegne.plus)