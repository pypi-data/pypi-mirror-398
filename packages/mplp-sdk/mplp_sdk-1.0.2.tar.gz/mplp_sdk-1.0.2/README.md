# MPLP Python SDK (`mplp-sdk`)

**Protocol:** MPLP v1.0.0 (Frozen)
**License:** Apache-2.0

The **MPLP Python SDK** provides a **protocol-compliant Python interface** for the
**Multi-Agent Lifecycle Protocol (MPLP)** — the Agent OS–level lifecycle specification for AI agent systems.

This package focuses on **schema-level correctness, model validation, and protocol alignment**.
It is designed to be used together with the official MPLP specification and documentation.

---

## Scope & Guarantees (Important)

### ✅ What this package provides

* **Protocol-compliant Python models** aligned with MPLP v1.0.0
* **Structural validation helpers** for core protocol objects (Context, Plan, Trace)
* **Strict version alignment** with the frozen MPLP protocol specification
* **Type-safe integration surface** for higher-level runtimes and tools

### ❌ What this package does NOT provide

* ❌ Full execution runtime (LLM orchestration, tool execution)
* ❌ Golden Flow execution engines (Flow-01 ~ Flow-05)
* ❌ Observability pipelines or distributed tracing backends
* ❌ Production agent orchestration

> These capabilities belong to **reference runtimes and products built *on top of* MPLP**,
> not to the protocol SDK itself.

---

## Installation

```bash
pip install mplp-sdk
```

---

## Basic Validation Usage

```python
from mplp import validate_context, validate_plan, validate_trace

result = validate_context({
    "protocolVersion": "1.0.0",
    # ...
})

if result.ok:
    print("Context is protocol-compliant")
else:
    print(result.errors)
```

> Validation helpers are provided to **assist protocol adoption**,
> not as a substitute for full lifecycle management.

---

## Protocol Documentation (Authoritative)

* **Homepage:** [https://mplp.io](https://mplp.io)
* **Specification & Docs:** [https://docs.mplp.io](https://docs.mplp.io)
* **Source Repository:** [https://github.com/Coregentis/MPLP-Protocol](https://github.com/Coregentis/MPLP-Protocol)
* **Issues:** [https://github.com/Coregentis/MPLP-Protocol/issues](https://github.com/Coregentis/MPLP-Protocol/issues)

All normative definitions, lifecycle semantics, and Golden Flows
are defined **exclusively** in the official documentation.

---

## Versioning & Compatibility

* **Protocol version:** MPLP v1.0.0 (Frozen)
* **SDK compatibility:** Guaranteed for v1.0.0 only
* Breaking changes require a new protocol version.

---

## License

Apache License, Version 2.0

© 2025 **Bangshi Beijing Network Technology Limited Company**
Coregentis AI
