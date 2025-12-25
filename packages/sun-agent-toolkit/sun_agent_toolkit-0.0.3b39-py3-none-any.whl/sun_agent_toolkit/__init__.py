"""
Sun Agent Toolkit

A comprehensive toolkit for building AI agents that interact with the TRON blockchain.
Provides wallet functionality, blockchain data access, and AI agent integrations.
"""

__version__ = "0.0.1"
__author__ = "Sun Agent Toolkit Team"

# Core exports
from . import adapters, core, plugins, wallets

__all__ = [
    "core",
    "wallets",
    "plugins",
    "adapters",
]
