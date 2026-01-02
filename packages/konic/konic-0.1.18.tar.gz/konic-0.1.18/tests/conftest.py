"""Pytest configuration and fixtures for konic tests."""

import pytest


@pytest.fixture(autouse=True)
def set_test_environment(monkeypatch):
    """
    Automatically set required environment variables for CLI tests.

    This fixture runs before each test and sets KONIC_HOST to a dummy value,
    allowing the KonicAPIClient to initialize without errors during test setup.
    The actual API calls are mocked in individual tests.
    """
    monkeypatch.setenv("KONIC_HOST", "http://test.konic.local")

    # Reset the lazy client instance to ensure each test starts fresh
    from konic.cli.client import client

    client._instance = None

    yield

    # Clean up after test
    client._instance = None
