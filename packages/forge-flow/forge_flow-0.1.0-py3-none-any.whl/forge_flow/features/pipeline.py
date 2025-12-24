"""Feature pipeline orchestrator for coordinating transformations.

Provides reproducible, versioned feature transformation workflows.
"""

from typing import Any

import pandas as pd
import structlog
from pydantic import BaseModel, Field

from forge_flow.exceptions import TransformationError
from forge_flow.features.cleaner import DataCleaner, NullStrategy
from forge_flow.features.engineer import FeatureEngineer

logger = structlog.get_logger(__name__)


class PipelineConfig(BaseModel):
    """Configuration for feature pipeline.

    Example:
        >>> config = PipelineConfig(
        ...     name="fraud_detection_v1",
        ...     entity="user_id",
        ...     window="30d",
        ...     null_strategy="fill_median",
        ...     remove_duplicates=True
        ... )
    """

    name: str = Field(description="Pipeline name/version")
    entity: str = Field(description="Entity column (e.g., 'user_id')")
    window: str | None = Field(default=None, description="Time window (e.g., '30d')")
    null_strategy: str = Field(default="drop", description="Null handling strategy")
    remove_duplicates: bool = Field(default=True, description="Remove duplicate rows")
    normalize_features: bool = Field(default=False, description="Normalize numerical features")


class FeaturePipeline:
    """Orchestrates feature transformation workflow.

    Coordinates cleaning, engineering, and validation steps in a
    reproducible, versioned manner.

    Example:
        >>> config = PipelineConfig(
        ...     name="user_features_v1",
        ...     entity="user_id",
        ...     null_strategy="fill_median"
        ... )
        >>> pipeline = FeaturePipeline(config)
        >>> features = pipeline.run(raw_data)
    """

    def __init__(self, config: PipelineConfig) -> None:
        """Initialize feature pipeline.

        Args:
            config: Pipeline configuration.
        """
        self.config = config
        self.cleaner = DataCleaner()
        self.engineer = FeatureEngineer()

        logger.info(
            "pipeline_initialized",
            name=config.name,
            entity=config.entity,
        )

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Execute complete feature pipeline.

        Args:
            df: Input DataFrame.

        Returns:
            Transformed DataFrame with ML-ready features.

        Raises:
            TransformationError: If pipeline execution fails.
        """
        try:
            logger.info(
                "pipeline_started",
                name=self.config.name,
                input_rows=len(df),
                input_columns=len(df.columns),
            )

            result = df.copy()

            # Step 1: Remove duplicates
            if self.config.remove_duplicates:
                result = self.cleaner.remove_duplicates(result)

            # Step 2: Handle nulls
            null_strategy = NullStrategy(self.config.null_strategy)
            result = self.cleaner.handle_nulls(result, strategy=null_strategy)

            # Step 3: Normalize if requested
            if self.config.normalize_features:
                numeric_cols = result.select_dtypes(include=["number"]).columns.tolist()
                if numeric_cols:
                    result = self.engineer.normalize(result, columns=numeric_cols)

            logger.info(
                "pipeline_complete",
                name=self.config.name,
                output_rows=len(result),
                output_columns=len(result.columns),
            )

            return result

        except Exception as e:
            logger.error(
                "pipeline_failed",
                name=self.config.name,
                error=str(e),
            )
            raise TransformationError(f"Pipeline {self.config.name} failed: {e}") from e

    def get_config(self) -> dict[str, Any]:
        """Get pipeline configuration as dictionary.

        Returns:
            Configuration dictionary.
        """
        return self.config.model_dump()
