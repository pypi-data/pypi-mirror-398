# 🔥 fireprompt

A lightweight Python library that turns functions into LLM prompts. Write Jinja2 templates, get type-safe Pydantic responses, and connect to 100+ providers via LiteLLM.


## Links:
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Callbacks](#callbacks)
- [Features](#features)


## Quick Start

```bash
pip install fireprompt
```

```python
from fireprompt import prompt, LLM
from pydantic import BaseModel

class ResearchResult(BaseModel):
    text: str

@prompt(
    model=LLM(
        name="openai/gpt-4o"
    )
)
def research_topic(topic: str, level: str = "basic") -> ResearchResult:
    """
    - role: system
      content: You are a helpful research assistant.

    - role: user
      content: >
        Analyze {{ topic }} at a {{ level }} level.
        Provide a clear and informative overview.
    """
    ...

result = research_topic(topic="Quantum Computing")
print(result.text)
```

**Output:**
```
Quantum computing is a revolutionary computing paradigm that leverages quantum mechanics
principles to process information. Unlike classical computers that use bits (0 or 1),
quantum computers use qubits that can exist in superposition, representing both states
simultaneously. This enables quantum computers to solve certain complex problems
exponentially faster than classical computers, particularly in cryptography, optimization,
and molecular simulation.
```

## Configuration

### Custom Parameters

Use `LLMConfig` for universal parameters across all providers:

```python
from fireprompt import prompt, LLM, LLMConfig
from pydantic import BaseModel

class Summary(BaseModel):
    text: str

@prompt(
    model=LLM(
        name="anthropic/claude-3-5-sonnet-20241022",
        config=LLMConfig(
            temperature=0.3,  # Lower = more focused (0-2)
            max_tokens=1000   # Max response length
        )
    )
)
def summarize(text: str, style: str = "professional", keywords: list[str] = []) -> Summary:
    """
    - role: system
      content: You are an expert text summarizer.

    - role: user
      content: |
        Summarize this text in {{ style | upper }} style.

        {% if keywords %}
        Focus on these keywords:
        {% for keyword in keywords %}
        - {{ keyword | title }}
        {% endfor %}
        {% endif %}

        Text:
        {{ text }}
    """
    ...

with open("article.txt") as f:
    result = summarize(
        text=f.read(),
        style="casual",
        keywords=[
            "AI",
            "Machine Learning",
            "Innovation"
        ]
    )

print(result.text)
```

### Provider-Specific Parameters

Use `extra` for provider-specific options:

```python
from fireprompt import prompt, LLM, LLMConfig
from pydantic import BaseModel

class Analysis(BaseModel):
    summary: str
    key_points: list[str]

@prompt(
    model=LLM(
        name="openai/gpt-4o",
        config=LLMConfig(
            temperature=0.7,
            extra={
                "frequency_penalty": 0.5,  # OpenAI-specific
                "presence_penalty": 0.3
            }
        )
    )
)
def analyze(text: str) -> Analysis:
    """
    - role: user
      content: Analyze this text: {{ text }}
    """
    ...

result = analyze("Your text here...")
print(result)
```

### Presets

Pre-configured settings for common use cases:

```python
from fireprompt import prompt, LLM, LLMConfigPreset
from pydantic import BaseModel

class BlogPost(BaseModel):
    title: str
    content: str

@prompt(
    model=LLM(
        name="gemini/gemini-1.5-pro",
        config=LLMConfigPreset.CREATIVE
    )
)
def write_blog(topic: str, sections: list[str] = []) -> BlogPost:
    """
    - role: user
      content: |
        Write an engaging blog post about {{ topic | title }}.

        {% if sections | length > 0 %}
        Include these sections:
        {% for section in sections %}
        {{ loop.index }}. {{ section }}
        {% endfor %}
        {% else %}
        Create your own structure.
        {% endif %}
    """
    ...

result = write_blog("Generative AI", sections=["Introduction", "Key Benefits", "Use Cases"])
print(result)
```

| Preset | Temperature | Top P | Best For |
|--------|-------------|-------|----------|
| `DEFAULT` | 0.7 | - | Balanced responses |
| `CREATIVE` | 0.9 | 0.95 | Writing, brainstorming |
| `PRECISE` | 0.3 | 0.9 | Technical analysis |
| `DETERMINISTIC` | 0.0 | 1.0 | Reproducible outputs |

## Callbacks

Post-process responses with `on_complete`:

```python
from fireprompt import prompt, LLM
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    score: float

def log_result(result: Analysis) -> Analysis:
    print(f"✓ {result.sentiment} ({result.score})")
    return result

@prompt(
    on_complete=log_result,
    model=LLM(
        name="openai/gpt-4o-mini"
    )
)
def analyze_sentiment(text: str) -> Analysis:
    """
    - role: user
      content: >
        Analyze sentiment: {{ text }}
        Return sentiment (positive/negative/neutral) and score (0-1).
    """
    ...

result = analyze_sentiment("I love this!")  # ✓ positive (0.95)
print(result)
```

## Debug Logging

```python
import fireprompt

fireprompt.enable_logging()   # Enable debug mode
fireprompt.disable_logging()  # Disable debug mode
```

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Type-Safe** | Automatic Pydantic validation for structured outputs |
| ⚡ **Async First** | Auto-detects and handles sync/async functions |
| 🎨 **Jinja2 Templates** | Full template support with variables, filters, loops, conditionals |
| 🔧 **Flexible Config** | Universal parameters + provider-specific options via `extra` |
| 📦 **Presets** | Pre-configured settings for common use cases |
| 🪝 **Callbacks** | Post-process responses with `on_complete` |
| 🔍 **Debug Mode** | Built-in logging for development |
| 🚀 **Multi-Provider** | 100+ LLMs via LiteLLM - OpenAI, Anthropic (Claude), Google (Gemini), Azure, AWS Bedrock, and more |
