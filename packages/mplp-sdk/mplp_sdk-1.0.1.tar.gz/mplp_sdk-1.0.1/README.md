# mplp-sdk

Python SDK and reference runtime for the MPLP Protocol v1.0.0 (Multi-Agent Lifecycle Protocol).

## Installation

```bash
pip install mplp-sdk
```

## Usage

```python
from mplp import validate_context, validate_plan, validate_trace

# Validate a context object
result = validate_context({"protocolVersion": "1.0.0", ...})
if result.ok:
    print("Valid!")
else:
    print("Errors:", result.errors)
```

## License

Apache-2.0

## Copyright

© 2025 Bangshi Beijing Network Technology Limited Company (Coregentis AI)

## Links

- Homepage: https://mplp.io
- Documentation: https://docs.mplp.io
- Repository: https://github.com/Coregentis/MPLP-Protocol
- Issues: https://github.com/Coregentis/MPLP-Protocol/issues
