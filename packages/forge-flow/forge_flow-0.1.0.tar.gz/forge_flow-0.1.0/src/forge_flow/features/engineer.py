"""Feature engineering utilities for creating ML-ready features.

Provides pure function transformations for feature extraction.
"""

import pandas as pd
import structlog
from sklearn.preprocessing import LabelEncoder, StandardScaler

from forge_flow.exceptions import TransformationError

logger = structlog.get_logger(__name__)


class FeatureEngineer:
    """Feature engineering with pure function transformations.

    All transformations are deterministic and depend only on input data
    and configuration, with no side effects.

    Example:
        >>> engineer = FeatureEngineer()
        >>> df = pd.DataFrame({
        ...     'user_id': [1, 1, 2, 2],
        ...     'amount': [100, 200, 150, 250],
        ...     'timestamp': pd.date_range('2024-01-01', periods=4)
        ... })
        >>>
        >>> # Add rolling window features
        >>> df = engineer.add_rolling_features(
        ...     df,
        ...     group_col='user_id',
        ...     value_col='amount',
        ...     windows=[2, 3]
        ... )
    """

    def add_rolling_features(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        windows: list[int],
        agg_funcs: list[str] | None = None,
    ) -> pd.DataFrame:
        """Add rolling window aggregation features.

        Args:
            df: Input DataFrame.
            group_col: Column to group by (e.g., 'user_id').
            value_col: Column to aggregate.
            windows: List of window sizes.
            agg_funcs: Aggregation functions ('mean', 'sum', 'std', 'min', 'max').

        Returns:
            DataFrame with new rolling features.

        Raises:
            TransformationError: If feature creation fails.
        """
        try:
            result = df.copy()
            agg_funcs = agg_funcs or ["mean", "sum"]

            logger.info(
                "adding_rolling_features",
                group_col=group_col,
                value_col=value_col,
                windows=windows,
            )

            for window in windows:
                for func in agg_funcs:
                    feature_name = f"{value_col}_rolling_{window}_{func}"

                    result[feature_name] = (
                        result.groupby(group_col)[value_col]
                        .rolling(window=window, min_periods=1)
                        .agg(func)
                        .reset_index(level=0, drop=True)
                    )

            logger.info("rolling_features_added", feature_count=len(windows) * len(agg_funcs))

            return result

        except Exception as e:
            logger.error("rolling_features_failed", error=str(e))
            raise TransformationError(f"Rolling feature creation failed: {e}") from e

    def add_lag_features(
        self,
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        lags: list[int],
    ) -> pd.DataFrame:
        """Add lag features.

        Args:
            df: Input DataFrame.
            group_col: Column to group by.
            value_col: Column to lag.
            lags: List of lag periods.

        Returns:
            DataFrame with new lag features.

        Raises:
            TransformationError: If feature creation fails.
        """
        try:
            result = df.copy()

            logger.info(
                "adding_lag_features",
                group_col=group_col,
                value_col=value_col,
                lags=lags,
            )

            for lag in lags:
                feature_name = f"{value_col}_lag_{lag}"
                result[feature_name] = result.groupby(group_col)[value_col].shift(lag)

            logger.info("lag_features_added", feature_count=len(lags))

            return result

        except Exception as e:
            logger.error("lag_features_failed", error=str(e))
            raise TransformationError(f"Lag feature creation failed: {e}") from e

    def encode_categorical(
        self,
        df: pd.DataFrame,
        columns: list[str],
        method: str = "label",
    ) -> pd.DataFrame:
        """Encode categorical variables.

        Args:
            df: Input DataFrame.
            columns: Columns to encode.
            method: Encoding method ('label' or 'onehot').

        Returns:
            DataFrame with encoded features.

        Raises:
            TransformationError: If encoding fails.
        """
        try:
            result = df.copy()

            logger.info(
                "encoding_categorical",
                columns=len(columns),
                method=method,
            )

            if method == "label":
                for col in columns:
                    if col not in result.columns:
                        continue

                    le = LabelEncoder()
                    result[f"{col}_encoded"] = le.fit_transform(result[col].astype(str))

            elif method == "onehot":
                result = pd.get_dummies(
                    result,
                    columns=columns,
                    prefix=columns,
                    drop_first=True,
                )

            else:
                raise TransformationError(f"Unknown encoding method: {method}")

            logger.info("categorical_encoded", method=method)

            return result

        except Exception as e:
            logger.error("categorical_encoding_failed", error=str(e))
            raise TransformationError(f"Categorical encoding failed: {e}") from e

    def normalize(
        self,
        df: pd.DataFrame,
        columns: list[str],
        method: str = "standard",
    ) -> pd.DataFrame:
        """Normalize numerical features.

        Args:
            df: Input DataFrame.
            columns: Columns to normalize.
            method: Normalization method ('standard' or 'minmax').

        Returns:
            DataFrame with normalized features.

        Raises:
            TransformationError: If normalization fails.
        """
        try:
            result = df.copy()

            logger.info(
                "normalizing_features",
                columns=len(columns),
                method=method,
            )

            if method == "standard":
                scaler = StandardScaler()
                for col in columns:
                    if col not in result.columns:
                        continue
                    if pd.api.types.is_numeric_dtype(result[col]):
                        result[f"{col}_normalized"] = scaler.fit_transform(result[[col]]).flatten()

            elif method == "minmax":
                for col in columns:
                    if col not in result.columns:
                        continue
                    if pd.api.types.is_numeric_dtype(result[col]):
                        min_val = result[col].min()
                        max_val = result[col].max()
                        result[f"{col}_normalized"] = (result[col] - min_val) / (max_val - min_val)

            else:
                raise TransformationError(f"Unknown normalization method: {method}")

            logger.info("features_normalized", method=method)

            return result

        except Exception as e:
            logger.error("normalization_failed", error=str(e))
            raise TransformationError(f"Normalization failed: {e}") from e

    def add_time_features(
        self,
        df: pd.DataFrame,
        datetime_col: str,
    ) -> pd.DataFrame:
        """Extract time-based features from datetime column.

        Args:
            df: Input DataFrame.
            datetime_col: Datetime column name.

        Returns:
            DataFrame with time features (hour, day, month, year, dayofweek).

        Raises:
            TransformationError: If feature extraction fails.
        """
        try:
            result = df.copy()

            logger.info("adding_time_features", datetime_col=datetime_col)

            # Ensure datetime type
            result[datetime_col] = pd.to_datetime(result[datetime_col])

            # Extract features
            result[f"{datetime_col}_hour"] = result[datetime_col].dt.hour
            result[f"{datetime_col}_day"] = result[datetime_col].dt.day
            result[f"{datetime_col}_month"] = result[datetime_col].dt.month
            result[f"{datetime_col}_year"] = result[datetime_col].dt.year
            result[f"{datetime_col}_dayofweek"] = result[datetime_col].dt.dayofweek
            result[f"{datetime_col}_quarter"] = result[datetime_col].dt.quarter

            logger.info("time_features_added", feature_count=6)

            return result

        except Exception as e:
            logger.error("time_features_failed", error=str(e))
            raise TransformationError(f"Time feature extraction failed: {e}") from e
