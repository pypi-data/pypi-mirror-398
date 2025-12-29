# Clarvynn OpenTelemetry Adapters

**Policy-based governance for OpenTelemetry telemetry.**

[![PyPI version](https://img.shields.io/pypi/v/clarvynn.svg)](https://pypi.org/project/clarvynn/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![OpenTelemetry SDK](https://img.shields.io/badge/opentelemetry--sdk-1.25.0--1.39.0-blue.svg)](https://opentelemetry.io/)

---

## What is Clarvynn?

Clarvynn provides **Deferred Head Sampling** for OpenTelemetry. It acts as a **Control Plane** that enforces **Purposeful Observability**, ensuring you capture high-fidelity signal without the high-volume noise.

**Result:** Keep 100% of critical signals (errors, slow requests) while sampling out the noise that distracts your team and bloats your storage. **This strategic reduction saves 60-80% on ingestion and indexing costs**, reallocating budget back to engineering capacity.

---

## Language Support

| Language | Status | Adapter |
|----------|--------|---------|
| **Python** | Production Ready | [`adapters/opentelemetry-python/`](adapters/opentelemetry-python/) |
| Java | Planned | - |
| Node.js | Planned | - |
| Go | Planned | - |

---

## Quick Start (Python)

### 1. Install

```bash
pip install clarvynn
```

### 2. Create Policy

```yaml
# policy.yaml
sampling:
  base_rate: 0.01  # 1% of routine traffic

conditions:
  - name: errors
    when: "status_code >= 400"
  - name: slow_requests
    when: "duration_ms > 1000"
```

### 3. Run

```bash
export CLARVYNN_ENABLED=true
export CLARVYNN_POLICY_PATH=policy.yaml
opentelemetry-instrument python app.py
```

**That's it.** Clarvynn is now intelligently sampling your telemetry.

---

## Key Features

- **Deferred Head Sampling** - Decisions made after request completion
- **Policy-driven** - Simple YAML configuration
- **Minimal overhead** - < 50µs per span evaluation
- **Drop-in** - Works with existing OTEL instrumentation
- **Distributed tracing** - W3C TraceContext Level 2 support
- **Signal Improvement** - High-Fidelity Signal, Low-Volume Noise
- **Log correlation** - Logs automatically follow trace sampling

---

## How It Works

Traditional sampling makes decisions **before** execution:

```
HEAD-BASED:  [Sample?] → Execute → [Don't know if it failed!]
                - Might drop errors
```

Clarvynn uses **Deferred Head Sampling** to decide **after** execution:

```
DEFERRED HEAD:  Execute → [Error? Slow?] → [Sample!]
                - Never miss critical signals
```

**Example:**

```yaml
# Your policy
conditions:
  - name: errors
    when: "status_code >= 500"
  
# What happens:
Request → Execute → Status: 500 → Exported (error captured)
Request → Execute → Status: 200 → 1% chance (base_rate)
```

---

## Documentation

**Getting Started:**
- [Quick Start](QUICKSTART.md) - 5-minute tutorial
- [Python Adapter](adapters/opentelemetry-python/README.md) - Python-specific docs

**Python Adapter Docs:**
- [Configuration](adapters/opentelemetry-python/docs/CONFIGURATION.md) - Python config reference
- [Frameworks](adapters/opentelemetry-python/docs/FRAMEWORKS.md) - Flask, Django, FastAPI
- [How It Works](adapters/opentelemetry-python/docs/HOW_IT_WORKS.md) - Python architecture

**Shared Documentation:**
- [CPL Reference](docs/CPL_REFERENCE.md) - Policy language (all languages)
- [W3C TraceContext Level 2](docs/W3C_LEVEL2.md) - Distributed tracing
- [Architecture](docs/ARCHITECTURE.md) - System design
- [Adapter Development](docs/ADAPTER_DEVELOPMENT.md) - Building new adapters

---

## Architecture

```
clarvynn/
├── core/                          # Shared CPL engine (all languages)
│   ├── cpl_engine/                # Policy evaluation logic
│   ├── policies/                  # Example policies
│   └── specs/                     # Language-agnostic specs
│
└── adapters/                      # Language-specific adapters
    ├── opentelemetry-python/      # Production ready
    ├── opentelemetry-java/        # Planned
    ├── opentelemetry-nodejs/      # Planned
    └── opentelemetry-go/          # Planned
```

**Design Philosophy:**

- `core/` = Language-agnostic policy engine and specifications
- `adapters/` = Language-specific OpenTelemetry integrations

Each adapter uses the same CPL policy format, ensuring consistent behavior across languages.

### Non-Blocking Architecture (Python)

Clarvynn operates as a **Lightweight Adapter** that ensures minimal impact on application performance by using a fully non-blocking export pipeline:

```
Request Ends
  ↓
ClarvynnSpanProcessor (Sync, ~2µs)
  ├─ 1. Evaluate CPL Policy (Keep/Drop)
  └─ 2. Inject TraceState (W3C Level 2)
  ↓
BatchExporterAdapter (Async Queue)
  ↓
Background Thread (Async)
  ↓
OTLPSpanExporter (Network I/O)
```

This architecture ensures that **governance decisions happen synchronously** (to decide before queuing), but **network I/O happens asynchronously** (to avoid blocking the application).

---

## Example: Multi-Service Deployment

Deploy the **same policy** across all services:

```yaml
# policy.yaml (use everywhere)
sampling:
  base_rate: 0.01

  conditions:
    - name: errors
      when: "status_code >= 400"
    - name: slow_requests
    when: "duration_ms > 1000"
```

**What happens:**

```
API Gateway (Python):
  └─ Error (500) → Exported + marked critical

Auth Service (Java):       # Coming Soon
  └─ Sees critical trace → Exported

Database Service (Go):     # Coming Soon
  └─ Sees critical trace → Exported

Result: Complete trace captured end-to-end
```

---

## Testing

Clarvynn has comprehensive test coverage (**336 tests, 100% pass rate**):

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=clarvynn --cov-report=html
```

See [`tests/README.md`](tests/README.md) for detailed testing guide.

---

## Compatibility

| Component | Supported Versions |
|-----------|-------------------|
| **Python** | 3.9, 3.10, 3.11, 3.12, 3.13 |
| **OpenTelemetry SDK** | 1.25.0 - 1.39.0 (tested) |
| **OpenTelemetry API** | 1.25.0 - 1.39.0 |

Compatibility is verified with automated testing. See `scripts/test_otel_compatibility.py`.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md).

**Adding a new language adapter?** See [Adapter Development Guide](docs/ADAPTER_DEVELOPMENT.md).

---

## License

Apache 2.0 - See [LICENSE](LICENSE)
