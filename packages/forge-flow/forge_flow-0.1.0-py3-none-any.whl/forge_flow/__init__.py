"""ForgeFlow: Engineering-First ML Library.

A composable Python library for building robust, engineering-grade machine learning pipelines.
Provides strict schema validation, point-in-time correct feature store, and resilient data connectors.

Focus: Correctness, Reproducibility, Type Safety.
"""

__version__ = "0.1.0"
__author__ = "ForgeFlow Contributors"
__license__ = "MIT"

# Public API - Lazy imports to avoid loading unnecessary dependencies
__all__ = [
    "__version__",
    # Exceptions
    "ForgeFlowError",
    "ValidationError",
    "IngestionError",
    "TransformationError",
    "ModelLoadError",
    "PredictionError",
    "ConfigurationError",
]


def __getattr__(name: str) -> object:
    """Lazy import for public API components."""
    if name in __all__:
        if name == "__version__":
            return __version__
        # Import exceptions
        from forge_flow.exceptions import (
            ConfigurationError,
            ForgeFlowError,
            IngestionError,
            ModelLoadError,
            PredictionError,
            TransformationError,
            ValidationError,
        )

        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
