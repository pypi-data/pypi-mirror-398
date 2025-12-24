# Emotionics
Emotionics is a **structural framework** for estimating emotional signals from text.  
It estimates — **it does not diagnose, judge, or determine emotions**.

Emotionics is designed to be:

- provider-neutral  
- responsibility-explicit  
- ethically constrained  

Emotionics focuses on **structure**, not authority.

## Quick Start (Recommended)
```python
import os
import emotionics

emotionics.activate(
    llm="openai",
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-5.2",
)

result = emotionics.estimate(
    text="今日も頑張る",
    mode="lite",
)

print(result)
```

Example output:
```python
{
  "mode": "lite",
  "version": "0.1.0",
  "trust": 0.6,
  "surprise": 0.1,
  "joy": 0.7,
  "fear": 0.1,
  "confidence": 0.75
}
```

⚠️ Emotionics does not ship API keys, models, or hosted services.
All LLM usage is explicitly controlled by the user.

## Installation
Install the released Lite version from PyPI:
```bash
pip install emotionics
```
Note: This repository is not intended for editable installs (pip install -e .).
Please use the PyPI package for standard installation and evaluation.

## What Emotionics Does
Emotionics provides:
	•	an emotional coordinate system
	•	an estimation framework
	•	a structured output schema

Emotionics does not:
	•	host models
	•	manage API keys
	•	store or transmit user data
	•	perform medical or psychological diagnosis

Emotionics is a framework, not a service.

## Usage
### Activation
Emotionics requires explicit activation before use.
```python
emotionics.activate(
    llm="openai",
    api_key="YOUR_OPENAI_API_KEY",
    model="gpt-5.2",
)
```
If activate() is not called, Emotionics raises:
```text
NotActivatedError
```
This is intentional.
Emotionics does not assume default providers or implicit API access.

### Estimation
```python
emotionics.estimate(
    text="今日も頑張る",
    mode="lite",
)
```

## Modes
### mode="lite" (Available)
	•	lightweight estimation
	•	low-cost
	•	minimal abstraction
	•	suitable for experiments and exploration

```python
emotionics.estimate(text="...", mode="lite")
```

### mode="full" (Not available in this build)
The full mode is reserved for future releases.
Attempting to use it will raise an error.

## LLM Providers

### Built-in Thin Wrapper (Recommended)
Currently supported:
	•	llm="openai"

```python
emotionics.activate(
    llm="openai",
    api_key="YOUR_OPENAI_API_KEY",
    model="gpt-5.2",
)
```

This wrapper internally constructs a provider while keeping
responsibility boundaries explicit.

## Provider Architecture (Advanced)
Emotionics itself does not depend on OpenAI, Gemini, or any specific SDK.

Internally, Emotionics expects a provider implementing:

```python
class LLMProvider:
    def generate(self, *, prompt: str, model: str, **kwargs) -> str:
        ...
```

### Example: User-Side OpenAI Provider
⚠️ This example is not part of the Emotionics library.
SDKs may change; this is shown for conceptual clarity only.
```python
from openai import OpenAI
import emotionics

class OpenAIProvider:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate(self, *, prompt: str, model: str, **kwargs) -> str:
        response = self.client.responses.create(
            model=model,
            input=prompt,
        )
        return response.output_text

emotionics.activate(
    provider=OpenAIProvider(api_key="YOUR_API_KEY"),
    model="gpt-5.2",
)
```

This path is intended for:
	•	custom providers
	•	research experimentation
	•	integration into larger systems

## Responsibility Boundary (Important)

Emotionics provides:
	•	emotional structure
	•	estimation logic
	•	schema definition

Users are responsible for:
	•	API key handling
	•	model choice
	•	cost control
	•	data privacy
	•	legal compliance

There is no hidden responsibility transfer.

## Ethical Notes
Emotionics estimates emotional signals from text.

It is not:
	•	a medical tool
	•	a diagnostic system
	•	a psychological authority

Do not:
	•	use it for diagnosis or treatment
	•	treat outputs as objective truth
	•	use it to manipulate or coerce individuals

Emotionics is intended for:
	•	research
	•	exploration
	•	reflective analysis
	•	abstract understanding of emotional tendencies

## Design Philosophy
Emotionics intentionally avoids bundling LLM SDKs.

Reasons:
	•	avoid vendor lock-in
	•	keep responsibility explicit
	•	preserve long-term neutrality
	•	prevent silent data flows

Emotionics does not aim to be the only correct implementation.
It is designed to be adapted, modified, and reinterpreted.

Only OpenAI has been tested by the author.
Other providers are intentionally left for community-driven implementations.

## Version
Emotionics v0.1.0

## Project & Contact
**Emotionics** is an experimental framework for estimating emotional signals from text.  
This repository provides the **Lite version** of Emotionics as a Python library, intended for research, experimentation, and technical evaluation.

The core design philosophy of Emotionics emphasizes:
- Estimation rather than judgment or diagnosis
- Structural interpretation of emotional patterns
- Clear separation between research, application, and ethical responsibility

### Source Repository
https://github.com/Kouhei-Takagi/emotionics

### Contact
If you are involved in research, governance, AI safety, or long-term foundational use of Emotionics,  
please contact:

📩 **info@project-saya.com**

Commercial exploitation, mass surveillance, or manipulative use is **not** the intended purpose of this project.