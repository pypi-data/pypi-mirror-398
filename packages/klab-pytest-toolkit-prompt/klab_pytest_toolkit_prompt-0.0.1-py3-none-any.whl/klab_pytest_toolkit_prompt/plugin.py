"""Pytest plugin to register prompt fixtures."""

from klab_pytest_toolkit_prompt.core import PromptFactory
import pytest


def pytest_configure(config):
    """Register custom markers and configure prompt fixtures."""
    pass


def pytest_addoption(parser):
    """Add command line and ini file options."""
    pass


@pytest.fixture
def prompt_factory() -> PromptFactory:
    """Factory fixture to create prompt interface instances.

    Returns:
        PromptFactory: An instance of the PromptFactory
    """
    return PromptFactory()
