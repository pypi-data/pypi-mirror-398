"""Quality gate for validating transformed data.

Ensures data quality meets thresholds before proceeding to training/serving.
"""

from typing import Any

import pandas as pd
import structlog
from pydantic import BaseModel, Field

from forge_flow.exceptions import TransformationError

logger = structlog.get_logger(__name__)


class QualityThresholds(BaseModel):
    """Quality thresholds for data validation.

    Example:
        >>> thresholds = QualityThresholds(
        ...     max_null_rate=0.01,
        ...     min_rows=1000,
        ...     max_cardinality={"category": 100}
        ... )
    """

    max_null_rate: float = Field(
        default=0.05, ge=0.0, le=1.0, description="Maximum allowed null rate (0-1)"
    )
    min_rows: int = Field(default=1, gt=0, description="Minimum required rows")
    max_cardinality: dict[str, int] | None = Field(
        default=None, description="Maximum cardinality per column"
    )
    required_columns: list[str] | None = Field(default=None, description="Required column names")


class QualityGate:
    """Validates data quality against defined thresholds.

    Acts as a safety valve to halt pipelines when data quality degrades
    beyond acceptable limits.

    Example:
        >>> thresholds = QualityThresholds(
        ...     max_null_rate=0.01,
        ...     min_rows=1000
        ... )
        >>> gate = QualityGate(thresholds)
        >>> gate.validate(df)  # Raises TransformationError if quality fails
    """

    def __init__(self, thresholds: QualityThresholds) -> None:
        """Initialize quality gate.

        Args:
            thresholds: Quality threshold configuration.
        """
        self.thresholds = thresholds

        logger.info(
            "quality_gate_initialized",
            max_null_rate=thresholds.max_null_rate,
            min_rows=thresholds.min_rows,
        )

    def validate(self, df: pd.DataFrame, raise_on_failure: bool = True) -> dict[str, bool]:
        """Validate DataFrame against quality thresholds.

        Args:
            df: DataFrame to validate.
            raise_on_failure: If True, raise exception on validation failure.

        Returns:
            Dictionary of check results (check_name -> passed).

        Raises:
            TransformationError: If validation fails and raise_on_failure=True.
        """
        results: dict[str, bool] = {}
        failures: list[str] = []

        logger.info("quality_validation_started", rows=len(df), columns=len(df.columns))

        # Check 1: Minimum rows
        results["min_rows"] = len(df) >= self.thresholds.min_rows
        if not results["min_rows"]:
            failures.append(f"Row count {len(df)} below minimum {self.thresholds.min_rows}")

        # Check 2: Null rate
        null_rate = df.isnull().sum().sum() / (len(df) * len(df.columns))
        results["null_rate"] = null_rate <= self.thresholds.max_null_rate
        if not results["null_rate"]:
            failures.append(
                f"Null rate {null_rate:.4f} exceeds maximum {self.thresholds.max_null_rate}"
            )

        # Check 3: Required columns
        if self.thresholds.required_columns:
            missing_cols = set(self.thresholds.required_columns) - set(df.columns)
            results["required_columns"] = len(missing_cols) == 0
            if not results["required_columns"]:
                failures.append(f"Missing required columns: {missing_cols}")

        # Check 4: Cardinality
        if self.thresholds.max_cardinality:
            cardinality_passed = True
            for col, max_card in self.thresholds.max_cardinality.items():
                if col in df.columns:
                    actual_card = df[col].nunique()
                    if actual_card > max_card:
                        cardinality_passed = False
                        failures.append(
                            f"Column {col} cardinality {actual_card} exceeds max {max_card}"
                        )

            results["cardinality"] = cardinality_passed

        # Log results
        passed_checks = sum(results.values())
        total_checks = len(results)

        logger.info(
            "quality_validation_complete",
            passed=passed_checks,
            total=total_checks,
            null_rate=f"{null_rate:.4f}",
        )

        # Raise if failures and configured to do so
        if failures and raise_on_failure:
            error_msg = "Quality validation failed:\n" + "\n".join(f"  - {f}" for f in failures)
            logger.error("quality_gate_failed", failures=failures)
            raise TransformationError(error_msg)

        return results

    def get_statistics(self, df: pd.DataFrame) -> dict[str, Any]:
        """Get data quality statistics.

        Args:
            df: DataFrame to analyze.

        Returns:
            Dictionary of quality statistics.
        """
        null_counts = df.isnull().sum()
        null_rate = null_counts.sum() / (len(df) * len(df.columns))

        stats = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "null_rate": null_rate,
            "null_counts_per_column": null_counts.to_dict(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

        # Add cardinality for object/category columns
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(categorical_cols) > 0:
            stats["cardinality"] = {col: df[col].nunique() for col in categorical_cols}

        return stats
