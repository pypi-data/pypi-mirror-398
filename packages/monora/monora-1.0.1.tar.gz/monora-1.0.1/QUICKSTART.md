# Monora v1 SDK - Quick Start Guide

## Installation

```bash
# Clone/navigate to the repo
cd Monora_beta

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the SDK
pip install -e .

# Install optional dependencies
pip install -e ".[yaml,https]"

# Install dev dependencies (for testing)
pip install -e ".[dev]"
```

## 5-Minute Tutorial

### Step 0: Generate a Config with the Wizard

```bash
monora init
```

This writes `monora.yml` in the current directory. Use `--yes` for defaults or `--force` to overwrite.

### Step 0a: Validate & Diagnose Config

```bash
monora validate --config monora.yml
monora doctor --config monora.yml
```

### Step 1: Basic Usage (Dev Mode)

Create `my_app.py`:

```python
import monora

# Initialize (uses stdout by default)
monora.init()

# Wrap your LLM calls
@monora.llm_call(purpose="customer_support")
def ask_ai(question: str, model: str = "gpt-4"):
    # Your LLM API call here
    return {"response": "Answer to " + question}

# Use trace context to group events
with monora.trace("ticket_123"):
    answer = ask_ai("How do I reset my password?")
    print(answer)
```

Run it:
```bash
python my_app.py
```

You'll see structured JSON events logged to stdout!

### Step 2: Add Policy Enforcement

Create `monora.yml`:

```yaml
policies:
  enforce: true
  model_allowlist:
    - "gpt-4*"
    - "claude-3-*"
  model_denylist:
    - "deepseek:*"

sinks:
  - type: file
    path: ./events.jsonl

alerts:
  violation_webhook: https://hooks.example.com/monora
  headers:
    Authorization: "Bearer ${MONORA_ALERTS_KEY}"
```

Update your app:

```python
import monora

# Initialize with config
monora.init(config_path="monora.yml")

# This will work
@monora.llm_call(purpose="test")
def allowed_call(model: str = "gpt-4"):
    return {"response": "ok"}

# This will raise PolicyViolation
@monora.llm_call(purpose="test")
def blocked_call(model: str = "deepseek-v3"):
    return {"response": "blocked"}

with monora.trace("test"):
    allowed_call()  # ✅ Works
    # blocked_call()  # ❌ Raises PolicyViolation
```

### Step 2a: Provider/Model Registry

Add to `monora.yml`:

```yaml
registry:
  version: "1.0.0"
  history:
    - version: "1.0.0"
      date: "2025-01-01"
      changes:
        - "Initial provider registry"
  default_provider: unknown
  allow_unknown: false  # log policy violation when no provider match
  providers:
    - name: openai
      model_patterns: ["gpt-*", "o1-*"]
      version_range: ">=1.0.0,<2.0.0"
      deprecated: false
    - name: anthropic
      model_patterns: ["claude-*"]
      version_range: ">=1.0.0,<2.0.0"
      deprecated: false
```

### Step 2b: Enforce Data Handling (Redaction/Block)

Add to `monora.yml`:

```yaml
data_handling:
  enabled: true
  mode: redact  # redact|block|allow
  rules:
    - name: email
      pattern: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"
      replace: "[REDACTED_EMAIL]"
      classifications: ["confidential", "secret"]
      apply_to: ["request", "response", "tool_args", "tool_result", "agent_input", "agent_output"]
```

With `mode: block`, Monora raises `DataHandlingViolation` before calling the LLM/tool if sensitive data is detected.

### Step 2c: Auto-Instrument OpenAI/Anthropic (Drop-in)

Add to `monora.yml`:

```yaml
instrumentation:
  enabled: true
  targets: ["openai", "anthropic"]
  default_purpose: general
  data_classification: null
```

When enabled, `monora.init()` patches supported SDK methods so calls are logged without manual decorators.
Async client methods are not auto-instrumented yet; use decorators for async flows.

### Step 3: Generate Compliance Reports

```bash
# Your app writes events to events.jsonl
python my_app.py

# Generate a JSON report
monora report --input events.jsonl --output report.json

# Generate a Markdown report
monora report --input events.jsonl --output report.md --format markdown

# Include policy config (reports unused allowlist patterns)
monora report --input events.jsonl --output report.json --format json --config monora.yml

# Generate a security review report (integrity + completeness)
monora security-review --input events.jsonl --output security.json --config monora.yml

# Generate a signed attestation bundle (GPG)
monora security-review --input events.jsonl --output security.json --config monora.yml \
  --sign gpg --gpg-key "you@example.com" --bundle security.bundle.json

Requires `gpg` installed and a configured signing key.

# View the report
cat report.json
```

For strict audit completeness, set `error_handling.queue_full_mode: block` and optional `buffering.queue_full_timeout_sec` to prevent drops on backpressure.

## Common Patterns

### Pattern 1: Classification-based Model Controls

```yaml
# monora.yml
policies:
  classification_max_models:
    secret:
      allowed:
        - "claude-3-opus-20240229"
```

```python
@monora.llm_call(
    data_classification="secret",
    purpose="pii_redaction"
)
def redact_pii(text: str, model: str = "claude-3-opus-20240229"):
    # Only Claude Opus allowed for secret data
    return redact(text, model)
```

### Pattern 2: Tool Call Tracking

```python
@monora.tool_call(
    tool_name="database_query",
    purpose="analytics"
)
def query_db(sql: str):
    return execute_query(sql)

with monora.trace("batch_job"):
    results = query_db("SELECT * FROM users")
```

### Pattern 3: Agent Workflows

```python
@monora.agent_step(
    agent_name="researcher",
    step_type="planning",
    purpose="research"
)
def plan_research(goal: str):
    return ["step1", "step2", "step3"]

@monora.agent_step(
    agent_name="researcher",
    step_type="execution",
    purpose="research"
)
def execute_step(step: str):
    return {"result": "..."}

with monora.trace("research_task"):
    plan = plan_research("Find latest AI papers")
    for step in plan:
        execute_step(step)
```

### Pattern 4: Violation Alerts

```python
def alert_security(violation: monora.PolicyViolation):
    print(f"🚨 ALERT: {violation.model} blocked!")
    # Send to Slack/PagerDuty/etc.

monora.set_violation_handler(alert_security)
```

## Testing Your Setup

Run the test suite:

```bash
pytest -v
```

Run the examples:

```bash
python examples/basic_usage.py
python examples/production_config.py
python examples/agent_workflow.py
```

## Next Steps

1. Read the [full README](README.md) for detailed API documentation
2. Check [MANIFEST.md](MANIFEST.md) for implementation details
3. Explore the [examples/](examples/) directory
4. Review the [monora.yml](monora.yml) sample configuration

## Troubleshooting

### "Module not found" errors

Make sure you've activated the virtual environment:
```bash
source .venv/bin/activate
```

### Tests failing

Reinstall dependencies:
```bash
pip install -e ".[dev]"
```

### Config not loading

Check file path and YAML syntax:
```bash
python -c "import yaml; print(yaml.safe_load(open('monora.yml')))"
```

## Support

- GitHub Issues: [github.com/monora/monora/issues](https://github.com/monora/monora/issues)
- Documentation: See README.md and MANIFEST.md in this repo

---

Happy tracing! 🔒🚀
