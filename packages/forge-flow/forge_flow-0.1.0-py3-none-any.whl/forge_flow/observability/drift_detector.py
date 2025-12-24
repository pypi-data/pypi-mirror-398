"""Drift detection for monitoring data distribution changes.

Detects statistical drift between training and serving data.
"""

from typing import Any

import numpy as np
import pandas as pd
import structlog
from scipy import stats

from forge_flow.exceptions import TransformationError

logger = structlog.get_logger(__name__)


class DriftDetector:
    """Detects statistical drift in data distributions.

    Uses Kolmogorov-Smirnov test and Population Stability Index (PSI)
    to detect distribution shifts between reference and current data.

    Example:
        >>> detector = DriftDetector()
        >>> # Set reference distribution (training data)
        >>> detector.set_reference(training_df)
        >>> # Check for drift in serving data
        >>> drift_results = detector.detect_drift(serving_df)
        >>> if drift_results['has_drift']:
        ...     print(f"Drift detected in columns: {drift_results['drifted_columns']}")
    """

    def __init__(self, significance_level: float = 0.05, psi_threshold: float = 0.1) -> None:
        """Initialize drift detector.

        Args:
            significance_level: P-value threshold for KS test (default: 0.05).
            psi_threshold: PSI threshold for drift detection (default: 0.1).
                          PSI < 0.1: No significant change
                          0.1 <= PSI < 0.2: Small change
                          PSI >= 0.2: Significant change
        """
        self.significance_level = significance_level
        self.psi_threshold = psi_threshold
        self.reference_stats: dict[str, Any] | None = None

        logger.info(
            "drift_detector_initialized",
            significance_level=significance_level,
            psi_threshold=psi_threshold,
        )

    def set_reference(self, df: pd.DataFrame) -> None:
        """Set reference distribution (typically training data).

        Args:
            df: Reference DataFrame.
        """
        self.reference_stats = {}

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                self.reference_stats[col] = {
                    "type": "numeric",
                    "mean": df[col].mean(),
                    "std": df[col].std(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "values": df[col].dropna().values,
                }
            else:
                # For categorical, store value counts
                value_counts = df[col].value_counts(normalize=True)
                self.reference_stats[col] = {
                    "type": "categorical",
                    "distribution": value_counts.to_dict(),
                }

        logger.info(
            "reference_set",
            columns=len(self.reference_stats),
            rows=len(df),
        )

    def detect_drift(
        self,
        df: pd.DataFrame,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect drift in current data compared to reference.

        Args:
            df: Current DataFrame to check for drift.
            columns: Optional list of columns to check (None = all columns).

        Returns:
            Dictionary with drift detection results:
            - has_drift: bool
            - drifted_columns: list[str]
            - drift_scores: dict[str, float]
            - details: dict with per-column statistics

        Raises:
            TransformationError: If reference not set or detection fails.
        """
        if self.reference_stats is None:
            raise TransformationError("Reference distribution not set. Call set_reference() first.")

        try:
            columns = columns or list(self.reference_stats.keys())
            drifted_columns = []
            drift_scores = {}
            details = {}

            logger.info("drift_detection_started", columns=len(columns))

            for col in columns:
                if col not in self.reference_stats:
                    logger.warning("column_not_in_reference", column=col)
                    continue

                if col not in df.columns:
                    logger.warning("column_not_in_current", column=col)
                    continue

                ref_stats = self.reference_stats[col]

                if ref_stats["type"] == "numeric":
                    # Use KS test for numeric columns
                    current_values = df[col].dropna().values
                    reference_values = ref_stats["values"]

                    if len(current_values) == 0:
                        continue

                    ks_stat, p_value = stats.ks_2samp(reference_values, current_values)

                    drift_scores[col] = ks_stat
                    details[col] = {
                        "test": "ks",
                        "statistic": ks_stat,
                        "p_value": p_value,
                        "drifted": p_value < self.significance_level,
                    }

                    if p_value < self.significance_level:
                        drifted_columns.append(col)

                else:
                    # Use PSI for categorical columns
                    current_dist = df[col].value_counts(normalize=True).to_dict()
                    reference_dist = ref_stats["distribution"]

                    psi = self._calculate_psi(reference_dist, current_dist)

                    drift_scores[col] = psi
                    details[col] = {
                        "test": "psi",
                        "psi": psi,
                        "drifted": psi >= self.psi_threshold,
                    }

                    if psi >= self.psi_threshold:
                        drifted_columns.append(col)

            has_drift = len(drifted_columns) > 0

            logger.info(
                "drift_detection_complete",
                has_drift=has_drift,
                drifted_columns=len(drifted_columns),
            )

            return {
                "has_drift": has_drift,
                "drifted_columns": drifted_columns,
                "drift_scores": drift_scores,
                "details": details,
            }

        except Exception as e:
            logger.error("drift_detection_failed", error=str(e))
            raise TransformationError(f"Drift detection failed: {e}") from e

    def _calculate_psi(
        self,
        reference_dist: dict[str, float],
        current_dist: dict[str, float],
    ) -> float:
        """Calculate Population Stability Index (PSI).

        Args:
            reference_dist: Reference distribution (value -> proportion).
            current_dist: Current distribution (value -> proportion).

        Returns:
            PSI value.
        """
        psi = 0.0
        epsilon = 1e-10  # Avoid log(0)

        # Get all unique values
        all_values = set(reference_dist.keys()) | set(current_dist.keys())

        for value in all_values:
            ref_prop = reference_dist.get(value, 0.0) + epsilon
            curr_prop = current_dist.get(value, 0.0) + epsilon

            psi += (curr_prop - ref_prop) * np.log(curr_prop / ref_prop)

        return psi
