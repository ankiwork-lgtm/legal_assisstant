"""Pytest configuration and shared fixtures for LegalLens AI test suite."""

import pytest

from app.limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate-limit counters before every test.

    Without this, tests running in the same process accumulate request counts
    against the same "testclient" IP and start returning 429 after 20 calls.
    """
    limiter.reset()
    yield
