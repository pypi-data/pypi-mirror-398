"""Serving module for online and offline feature stores.

Provides low-latency feature retrieval for ML serving.
"""

from forge_flow.serving.online_store import OnlineStore

__all__ = ["OnlineStore"]
