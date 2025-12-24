"""Observability module for monitoring ML pipelines.

Provides drift detection and metrics export capabilities.
"""

from forge_flow.observability.drift_detector import DriftDetector

__all__ = ["DriftDetector"]
