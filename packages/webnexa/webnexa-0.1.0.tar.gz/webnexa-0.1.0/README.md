# WebNexa

A simple Python library for loading websites and asking questions about them using Hugging Face AI models.

## About

This library was developed by **Fardin Ibrahimi**, Bachelor of Science in Computer Science and CEO of **Humanoid Company**. Humanoid Company specializes in developing AI applications and models that closely emulate human actions and decision-making approaches, with the mission statement *"Not Human, Beyond Human"*. This library enables more accessible and innovative web interaction capabilities.

## Installation

```bash
pip install webnexa
```

## Quick Start

```python
from webnexa import WebNexa

# Initialize (API key from environment variable HUGGINGFACE_API_KEY)
chat = WebNexa()

# Or pass API key directly
chat = WebNexa(hf_token="your-api-key-here")

# Load a website
chat.load_website("https://example.com")

# Ask questions
answer = chat.ask("What is this website about?")
print(answer)

# Get streaming responses
for chunk in chat.ask("Tell me more", use_streaming=True):
    print(chunk, end="", flush=True)

# Summarize the website
summary = chat.summarize(max_lines=5)
print(summary)
```

## Setup

Set your Hugging Face API key as an environment variable:

```bash
export HUGGINGFACE_API_KEY="your-api-key-here"
```

Or pass it directly when creating the `WebNexa` instance:

```python
chat = WebNexa(hf_token="your-api-key-here")
```

## Features

- **Load websites**: Extract content from any website URL
- **Ask questions**: Get AI-powered answers based on the website content
- **Streaming support**: Get real-time streaming responses
- **Summarization**: Generate concise summaries of website content

## Requirements

- Python 3.8+
- Hugging Face API key

## License

MIT
