"""Pytest configuration — set required env vars before any app module is imported."""

import os

# Provide a dummy key so app.config.Settings() doesn't raise during test collection.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-in-unit-tests")
