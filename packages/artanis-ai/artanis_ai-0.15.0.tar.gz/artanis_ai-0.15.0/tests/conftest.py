"""Pytest configuration and fixtures."""

import pytest
import os


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean Artanis environment variables before each test."""
    monkeypatch.delenv("ARTANIS_API_KEY", raising=False)
    monkeypatch.delenv("ARTANIS_BASE_URL", raising=False)
    monkeypatch.delenv("ARTANIS_ENABLED", raising=False)
    monkeypatch.delenv("ARTANIS_DEBUG", raising=False)
