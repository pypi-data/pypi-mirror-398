# Klab Pytest Toolkit - Decorators

Custom pytest decorators for marking and annotating tests.

At the moment the package provides the following decorator:

- `@requirement(id: str)`: Marks a test with a requirement ID for traceability. The ID is added to the junit xml output.

## Installation

```bash
pip install klab_pytest_toolkit_decorators
```

## Usage

### Requirement Decorator

Mark tests with requirement IDs for traceability:

```python
from klab_pytest_toolkit_decorators import requirement

@requirement("REQ-001")
def test_something():
    assert True

@requirement("REQ-002")
async def test_async_something():
    assert True
```

The decorator works with both synchronous and asynchronous test functions. The requirement IDs are added to the junit xml output.

## License

MIT
