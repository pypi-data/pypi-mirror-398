"""File connector for reading various file formats.

Supports local files and cloud storage (S3, GCS, Azure) via fsspec.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import structlog

from forge_flow.exceptions import IngestionError
from forge_flow.ingestion.base import DataSource

logger = structlog.get_logger(__name__)


class FileConnector(DataSource):
    """Connector for reading files in various formats.

    Supports:
    - Parquet (recommended for large datasets)
    - CSV
    - JSON
    - Local filesystem and cloud storage (S3, GCS, Azure)

    Example:
        >>> # Read local Parquet file
        >>> connector = FileConnector()
        >>> df = connector.read_parquet("data/transactions.parquet")
        >>>
        >>> # Read from S3
        >>> df = connector.read_parquet("s3://bucket/data/transactions.parquet")
        >>>
        >>> # Read CSV with custom options
        >>> df = connector.read_csv("data/users.csv", parse_dates=["created_at"])
    """

    def __init__(self, storage_options: dict[str, Any] | None = None) -> None:
        """Initialize file connector.

        Args:
            storage_options: Optional storage configuration for cloud providers.
                           For S3: {"key": "...", "secret": "..."}
                           For GCS: {"token": "..."}
        """
        self.storage_options = storage_options or {}

    def fetch(self) -> pd.DataFrame:
        """Not implemented for FileConnector.

        Use specific read methods (read_parquet, read_csv, read_json) instead.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError(
            "FileConnector requires explicit format method. "
            "Use read_parquet(), read_csv(), or read_json()"
        )

    def read_parquet(
        self,
        path: str | Path,
        columns: list[str] | None = None,
        filters: list[tuple[str, str, Any]] | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Read Parquet file(s).

        Args:
            path: File path (local or cloud URL).
            columns: Optional list of columns to read (for efficiency).
            filters: Optional row filters in PyArrow format.
            **kwargs: Additional arguments passed to pd.read_parquet.

        Returns:
            DataFrame containing the data.

        Raises:
            IngestionError: If reading fails.
        """
        try:
            logger.info("reading_parquet", path=str(path), columns=columns)

            df = pd.read_parquet(
                path,
                columns=columns,
                filters=filters,
                storage_options=self.storage_options,
                **kwargs,
            )

            logger.info(
                "parquet_read_complete",
                path=str(path),
                rows=len(df),
                columns=len(df.columns),
            )

            return df

        except Exception as e:
            logger.error("parquet_read_failed", path=str(path), error=str(e))
            raise IngestionError(f"Failed to read Parquet file {path}: {e}") from e

    def read_csv(
        self,
        path: str | Path,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Read CSV file.

        Args:
            path: File path (local or cloud URL).
            **kwargs: Additional arguments passed to pd.read_csv.

        Returns:
            DataFrame containing the data.

        Raises:
            IngestionError: If reading fails.
        """
        try:
            logger.info("reading_csv", path=str(path))

            df = pd.read_csv(
                path,
                storage_options=self.storage_options,
                **kwargs,
            )

            logger.info(
                "csv_read_complete",
                path=str(path),
                rows=len(df),
                columns=len(df.columns),
            )

            return df

        except Exception as e:
            logger.error("csv_read_failed", path=str(path), error=str(e))
            raise IngestionError(f"Failed to read CSV file {path}: {e}") from e

    def read_json(
        self,
        path: str | Path,
        orient: str = "records",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Read JSON file.

        Args:
            path: File path (local or cloud URL).
            orient: JSON orientation ('records', 'index', 'columns', etc.).
            **kwargs: Additional arguments passed to pd.read_json.

        Returns:
            DataFrame containing the data.

        Raises:
            IngestionError: If reading fails.
        """
        try:
            logger.info("reading_json", path=str(path), orient=orient)

            df = pd.read_json(
                path,
                orient=orient,
                storage_options=self.storage_options,
                **kwargs,
            )

            logger.info(
                "json_read_complete",
                path=str(path),
                rows=len(df),
                columns=len(df.columns),
            )

            return df

        except Exception as e:
            logger.error("json_read_failed", path=str(path), error=str(e))
            raise IngestionError(f"Failed to read JSON file {path}: {e}") from e

    def write_parquet(
        self,
        df: pd.DataFrame,
        path: str | Path,
        compression: str = "snappy",
        **kwargs: Any,
    ) -> None:
        """Write DataFrame to Parquet file.

        Args:
            df: DataFrame to write.
            path: Output file path (local or cloud URL).
            compression: Compression algorithm ('snappy', 'gzip', 'brotli', 'zstd').
            **kwargs: Additional arguments passed to pd.to_parquet.

        Raises:
            IngestionError: If writing fails.
        """
        try:
            logger.info(
                "writing_parquet",
                path=str(path),
                rows=len(df),
                compression=compression,
            )

            df.to_parquet(
                path,
                compression=compression,
                storage_options=self.storage_options,
                index=False,
                **kwargs,
            )

            logger.info("parquet_write_complete", path=str(path))

        except Exception as e:
            logger.error("parquet_write_failed", path=str(path), error=str(e))
            raise IngestionError(f"Failed to write Parquet file {path}: {e}") from e
