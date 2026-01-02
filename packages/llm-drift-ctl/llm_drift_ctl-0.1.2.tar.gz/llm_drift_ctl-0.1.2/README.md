# llm-drift-ctl (Python)

> **llm-drift-ctl is a drop-in guard that validates LLM outputs using your own LLM when needed — and no LLM when not.**

Production-grade LLM output validation package for Python. This package **does NOT generate content**. It **validates LLM outputs** after they are produced.

## Installation

```bash
pip install llm-drift-ctl
```

## Quick Start

### FORMAT Mode (LLM-free, fully offline)

```python
from llm_drift_ctl import DriftGuard, DriftGuardConfig

guard = DriftGuard(DriftGuardConfig(pipeline_id="my-pipeline"))

# Check JSON format (using keyword arguments)
result = await guard.check(
    json={"name": "John", "age": 30},
    mode="FORMAT"
)

# Or using CheckInput object
from llm_drift_ctl import CheckInput
result = await guard.check(
    CheckInput(json={"name": "John", "age": 30}, mode="FORMAT")
)

print(result)
# CheckResult(
#     block=False,
#     decision='ALLOW',
#     severity='LOW',
#     scores={'format': 1.0},
#     where=[]
# )
```

### CONTENT Mode (requires your LLM)

```python
from llm_drift_ctl import DriftGuard, DriftGuardConfig, UserLLM

# Implement your LLM adapter
class MyLLM(UserLLM):
    async def generate(self, prompt, text=None, json=None):
        # Call OpenAI, Gemini, Claude, or your custom LLM
        # You provide your own API key
        return "response from your LLM"

guard = DriftGuard(DriftGuardConfig(
    pipeline_id="my-pipeline",
    llm=MyLLM(),
    api_key="your-license-key"  # for cloud license verification
))

# Accept a baseline (approved output)
await guard.accept_baseline(json={"name": "John", "age": 30})

# Check against baseline
result = await guard.check(
    json={"name": "Jane", "age": 25},
    mode="CONTENT"
)
```

## API Reference

See the main [README.md](../README.md) for full documentation.

The Python API mirrors the Node.js API exactly.

## License

MIT

