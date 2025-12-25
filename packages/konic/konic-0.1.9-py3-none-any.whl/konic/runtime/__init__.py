"""Konic Runtime - Agent and Data Registration Module.

This module provides functions for registering agents and data dependencies
that will be resolved at training time by the Konic Cloud Platform engine.

Example:
    >>> from konic.runtime import register_agent, register_data
    >>> from konic.agent import KonicAgent
    >>>
    >>> # Register data dependencies
    >>> register_data("stock-prices", "STOCK_DATA_PATH", "1.0.0")
    >>> register_data("market-indicators", "INDICATORS_PATH", "latest")
    >>>
    >>> # Register the agent
    >>> agent = KonicAgent(environment=MyEnvironment())
    >>> register_agent(agent, name="trading-agent")
"""

from konic.runtime.agent import get_registered_agent, register_agent
from konic.runtime.data import get_registered_data, register_data

__all__ = [
    "register_agent",
    "get_registered_agent",
    "register_data",
    "get_registered_data",
]
