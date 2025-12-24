"""Data cleaning utilities with immutable operations.

All cleaning operations return new DataFrames without modifying the input.
"""

from enum import Enum
from typing import Any

import pandas as pd
import structlog

from forge_flow.exceptions import TransformationError

logger = structlog.get_logger(__name__)


class NullStrategy(str, Enum):
    """Strategies for handling null values."""

    DROP = "drop"
    FILL_MEAN = "fill_mean"
    FILL_MEDIAN = "fill_median"
    FILL_MODE = "fill_mode"
    FILL_CONSTANT = "fill_constant"
    FILL_FORWARD = "fill_forward"
    FILL_BACKWARD = "fill_backward"


class OutlierStrategy(str, Enum):
    """Strategies for handling outliers."""

    IQR = "iqr"
    PERCENTILE = "percentile"
    Z_SCORE = "z_score"


class DataCleaner:
    """Immutable data cleaning operations.

    All methods return new DataFrames without modifying the input,
    following functional programming principles.

    Example:
        >>> cleaner = DataCleaner()
        >>> df = pd.DataFrame({'age': [25, None, 30], 'income': [50000, 60000, 1000000]})
        >>>
        >>> # Remove nulls
        >>> clean_df = cleaner.handle_nulls(df, strategy=NullStrategy.FILL_MEDIAN)
        >>>
        >>> # Cap outliers
        >>> clean_df = cleaner.cap_outliers(clean_df, columns=['income'], strategy=OutlierStrategy.IQR)
    """

    def handle_nulls(
        self,
        df: pd.DataFrame,
        strategy: NullStrategy = NullStrategy.DROP,
        columns: list[str] | None = None,
        fill_value: Any = None,
    ) -> pd.DataFrame:
        """Handle null values using specified strategy.

        Args:
            df: Input DataFrame.
            strategy: Null handling strategy.
            columns: Optional list of columns to process (None = all columns).
            fill_value: Value to use for FILL_CONSTANT strategy.

        Returns:
            New DataFrame with nulls handled.

        Raises:
            TransformationError: If strategy fails.
        """
        try:
            result = df.copy()
            target_cols = columns or df.columns.tolist()

            logger.info(
                "handling_nulls",
                strategy=strategy.value,
                columns=len(target_cols),
                null_count=df[target_cols].isnull().sum().sum(),
            )

            if strategy == NullStrategy.DROP:
                result = result.dropna(subset=target_cols)

            elif strategy == NullStrategy.FILL_MEAN:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(result[col]):
                        result[col] = result[col].fillna(result[col].mean())

            elif strategy == NullStrategy.FILL_MEDIAN:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(result[col]):
                        result[col] = result[col].fillna(result[col].median())

            elif strategy == NullStrategy.FILL_MODE:
                for col in target_cols:
                    mode_val = result[col].mode()
                    if not mode_val.empty:
                        result[col] = result[col].fillna(mode_val[0])

            elif strategy == NullStrategy.FILL_CONSTANT:
                if fill_value is None:
                    raise TransformationError("fill_value required for FILL_CONSTANT strategy")
                result[target_cols] = result[target_cols].fillna(fill_value)

            elif strategy == NullStrategy.FILL_FORWARD:
                result[target_cols] = result[target_cols].fillna(method="ffill")

            elif strategy == NullStrategy.FILL_BACKWARD:
                result[target_cols] = result[target_cols].fillna(method="bfill")

            logger.info(
                "nulls_handled",
                strategy=strategy.value,
                remaining_nulls=result[target_cols].isnull().sum().sum(),
            )

            return result

        except Exception as e:
            logger.error("null_handling_failed", strategy=strategy.value, error=str(e))
            raise TransformationError(f"Null handling failed: {e}") from e

    def cap_outliers(
        self,
        df: pd.DataFrame,
        columns: list[str],
        strategy: OutlierStrategy = OutlierStrategy.IQR,
        lower_percentile: float = 0.01,
        upper_percentile: float = 0.99,
        z_threshold: float = 3.0,
    ) -> pd.DataFrame:
        """Cap outliers using specified strategy.

        Args:
            df: Input DataFrame.
            columns: Columns to process.
            strategy: Outlier handling strategy.
            lower_percentile: Lower percentile for PERCENTILE strategy.
            upper_percentile: Upper percentile for PERCENTILE strategy.
            z_threshold: Z-score threshold for Z_SCORE strategy.

        Returns:
            New DataFrame with outliers capped.

        Raises:
            TransformationError: If strategy fails.
        """
        try:
            result = df.copy()

            logger.info(
                "capping_outliers",
                strategy=strategy.value,
                columns=len(columns),
            )

            for col in columns:
                if not pd.api.types.is_numeric_dtype(result[col]):
                    logger.warning("skipping_non_numeric_column", column=col)
                    continue

                if strategy == OutlierStrategy.IQR:
                    Q1 = result[col].quantile(0.25)
                    Q3 = result[col].quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR

                elif strategy == OutlierStrategy.PERCENTILE:
                    lower_bound = result[col].quantile(lower_percentile)
                    upper_bound = result[col].quantile(upper_percentile)

                elif strategy == OutlierStrategy.Z_SCORE:
                    mean = result[col].mean()
                    std = result[col].std()
                    lower_bound = mean - z_threshold * std
                    upper_bound = mean + z_threshold * std

                else:
                    raise TransformationError(f"Unknown outlier strategy: {strategy}")

                # Cap values
                result[col] = result[col].clip(lower=lower_bound, upper=upper_bound)

            logger.info("outliers_capped", strategy=strategy.value)

            return result

        except Exception as e:
            logger.error("outlier_capping_failed", strategy=strategy.value, error=str(e))
            raise TransformationError(f"Outlier capping failed: {e}") from e

    def cast_types(
        self,
        df: pd.DataFrame,
        type_map: dict[str, str],
    ) -> pd.DataFrame:
        """Cast column types with validation.

        Args:
            df: Input DataFrame.
            type_map: Mapping of column names to target types.

        Returns:
            New DataFrame with casted types.

        Raises:
            TransformationError: If type casting fails.
        """
        try:
            result = df.copy()

            logger.info("casting_types", columns=len(type_map))

            for col, dtype in type_map.items():
                if col not in result.columns:
                    logger.warning("column_not_found", column=col)
                    continue

                result[col] = result[col].astype(dtype)

            logger.info("types_casted")

            return result

        except Exception as e:
            logger.error("type_casting_failed", error=str(e))
            raise TransformationError(f"Type casting failed: {e}") from e

    def remove_duplicates(
        self,
        df: pd.DataFrame,
        subset: list[str] | None = None,
        keep: str = "first",
    ) -> pd.DataFrame:
        """Remove duplicate rows.

        Args:
            df: Input DataFrame.
            subset: Optional columns to consider for duplicates.
            keep: Which duplicates to keep ('first', 'last', False).

        Returns:
            New DataFrame without duplicates.
        """
        result = df.copy()

        logger.info(
            "removing_duplicates",
            total_rows=len(result),
            subset=subset,
        )

        result = result.drop_duplicates(subset=subset, keep=keep)

        logger.info(
            "duplicates_removed",
            remaining_rows=len(result),
            removed=len(df) - len(result),
        )

        return result
