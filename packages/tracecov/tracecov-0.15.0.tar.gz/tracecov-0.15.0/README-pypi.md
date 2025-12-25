# TraceCov

**Schema-level API coverage down to individual keywords.**

Your API tests pass. But did you actually test the validation rules?

Hitting `POST /users` with `{"name": "Alice", "age": 30}` gives you 100% endpoint coverage—but you haven't tested empty names, negative ages, or strings that are too long.

TraceCov measures coverage at the **schema keyword level**: `minLength`, `pattern`, `enum`, `minimum` - not just endpoints.

![API Coverage Report](https://docs.tracecov.sh/report-demo.png)

## Install

```bash
pip install tracecov
```

## Quick Start

```python
import tracecov
import requests

# Load your OpenAPI schema
coverage = tracecov.CoverageMap.from_path("openapi.json")

# Wrap your session to track requests
session = coverage.requests.track_session(requests.Session())

# Run your tests as usual
session.post("https://api.example.com/users", json={"name": "Alice"})
session.get("https://api.example.com/users/123")

# Generate the report
coverage.save_report()
```

## What It Tracks

| Dimension | What it measures |
|-----------|------------------|
| **Operations** | HTTP method + path combinations called |
| **Parameters** | Path, query, header, cookie, body coverage |
| **Keywords** | JSON Schema validation rules (`minLength`, `pattern`, etc.) |
| **Examples** | Schema examples and defaults used |
| **Responses** | HTTP status codes returned |

## Documentation

https://docs.tracecov.sh/

## Feedback

Help shape TraceCov: [2-minute survey](https://forms.gle/53Zcpt4NxbvmXbwFA)

## Professional Edition

For advanced features, contact info@tracecov.sh.
