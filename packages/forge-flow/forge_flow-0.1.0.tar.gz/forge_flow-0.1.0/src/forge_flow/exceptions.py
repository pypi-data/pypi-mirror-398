"""Custom exceptions for ForgeFlow."""


class ForgeFlowError(Exception):
    """Base exception for all ForgeFlow errors."""

    pass


class ValidationError(ForgeFlowError):
    """Raised when data validation fails."""

    def __init__(self, message: str, invalid_rows: int = 0, total_rows: int = 0):
        self.invalid_rows = invalid_rows
        self.total_rows = total_rows
        super().__init__(message)


class IngestionError(ForgeFlowError):
    """Raised when data ingestion fails."""

    pass


class TransformationError(ForgeFlowError):
    """Raised when feature transformation fails."""

    pass


class ModelLoadError(ForgeFlowError):
    """Raised when model loading fails."""

    pass


class PredictionError(ForgeFlowError):
    """Raised when prediction fails."""

    pass


class ConfigurationError(ForgeFlowError):
    """Raised when configuration is invalid."""

    pass


class FeatureStoreError(ForgeFlowError):
    """Raised when feature store operations fail."""

    pass
