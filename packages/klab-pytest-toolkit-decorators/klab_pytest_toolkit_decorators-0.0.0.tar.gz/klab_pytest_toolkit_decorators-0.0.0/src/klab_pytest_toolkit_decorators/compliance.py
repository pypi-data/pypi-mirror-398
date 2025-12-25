import functools
import inspect
from collections.abc import Awaitable, Callable

import pytest


def requirement(*req_ids):
    """Custom decorator to mark a test with requirement ID(s) and log them in the JUnit report.

    Supports multiple requirements in several ways:
    - Single requirement: @requirement("REQ-001")
    - Multiple arguments: @requirement("REQ-001", "REQ-002", "REQ-003")
    - Multiple decorators: @requirement("REQ-001") @requirement("REQ-002")
    """
    if not req_ids:
        raise ValueError("At least one requirement ID must be provided")

    def decorator(func: Callable) -> Callable[[], Awaitable[None]]:
        # Apply markers for each requirement ID at decoration time
        marked_func = func
        for req_id in req_ids:
            marked_func = pytest.mark.requirement(req_id)(marked_func)

        @functools.wraps(marked_func)
        async def async_wrapper(*args, **kwargs):
            return await marked_func(*args, **kwargs)

        @functools.wraps(marked_func)
        def sync_wrapper(*args, **kwargs):
            return marked_func(*args, **kwargs)

        wrapper = async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
        # Copy over the pytest markers to the wrapper
        # type: ignore is needed because pytestmark is dynamically added
        setattr(wrapper, "pytestmark", getattr(marked_func, "pytestmark", []))
        return wrapper

    return decorator
