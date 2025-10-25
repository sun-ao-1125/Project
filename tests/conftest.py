"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio test"
    )
