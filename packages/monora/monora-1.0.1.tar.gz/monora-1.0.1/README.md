# Monora v1 SDK

**Lightweight governance and trace SDK for AI systems**

Monora provides minimal viable trust through immutable event logs, policy enforcement, and comprehensive auditability for LLM applications.

## Features

- **🔒 Immutable Event Logs**: Cryptographic hash chains for tamper detection
- **📋 Policy Enforcement**: Model allowlists/denylists with data classification controls
- **🧭 Provider Registry**: Explicit model-to-provider mapping with unknown-model alerts
- **🧾 Versioned Registry**: Registry versioning, history, and provider deprecation metadata
- **🔍 Full Auditability**: JSON-lines event logs with CLI reporting tools
- **⚡ Non-blocking**: Background worker with bounded queue for zero user-code latency
- **🎯 Simple API**: Decorator-based interface with sensible defaults
- **🧩 Auto-Instrumentation**: Optional OpenAI/Anthropic patching for drop-in logging
- **✅ Completeness Checks**: Event sequencing and security review reports
- **🔌 Pluggable Sinks**: Stdout, file, and HTTPS endpoints
- **🚨 Violation Alerts**: Callback or webhook notifications for policy violations
- **🧹 Data Handling**: Regex redaction rules tied to data classifications
- **🛡️ Signed Attestations**: Optional GPG-signed security review bundles

## Installation

```bash
pip install -e .

# With YAML config support
pip install -e ".[yaml]"

# With HTTPS sink support
pip install -e ".[https]"

# Development dependencies
pip install -e ".[dev]"
```

## Quick Start

### Minimal Example (Dev Mode)

```python
import monora

# Initialize with defaults (stdout logging, no policies)
monora.init()

@monora.llm_call(purpose="customer_support")
def ask_gpt(prompt: str, model: str = "gpt-4o-mini"):
    # Your LLM call here
    return {"response": "Hello!"}

# Use trace context for grouping events
with monora.trace("ticket_123"):
    response = ask_gpt("How do I reset my password?")
```

### Guided Setup (Wizard)

```bash
monora init
```

This generates a `monora.yml` you can edit and pass to `monora.init(config_path="monora.yml")`.

### Validate & Diagnose

```bash
monora validate --config monora.yml
monora doctor --config monora.yml
```

See README.md for full documentation and examples.

## Testing

```bash
pytest
```

## License

MIT
