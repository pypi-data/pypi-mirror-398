"""Database connector with watermark-based incremental loading.

Supports PostgreSQL, MySQL, and other SQLAlchemy-compatible databases.
"""

from datetime import datetime
from typing import Any

import pandas as pd
import structlog

from forge_flow.exceptions import IngestionError
from forge_flow.ingestion.base import DataSource

logger = structlog.get_logger(__name__)


class DBConnector(DataSource):
    """Database connector with incremental loading support.

    Features:
    - Watermark-based incremental queries
    - Connection pooling via SQLAlchemy
    - Automatic type inference
    - Chunked reading for large result sets

    Example:
        >>> from sqlalchemy import create_engine
        >>> engine = create_engine("postgresql://user:pass@localhost/db")
        >>> connector = DBConnector(engine)
        >>>
        >>> # Full load
        >>> df = connector.query("SELECT * FROM users")
        >>>
        >>> # Incremental load
        >>> df = connector.incremental_query(
        ...     table="events",
        ...     watermark_column="created_at",
        ...     last_watermark="2024-01-01"
        ... )
    """

    def __init__(self, engine: Any) -> None:
        """Initialize database connector.

        Args:
            engine: SQLAlchemy engine instance.
        """
        self.engine = engine

    def fetch(self) -> pd.DataFrame:
        """Not implemented for DBConnector.

        Use query() or incremental_query() instead.

        Raises:
            NotImplementedError: Always raised.
        """
        raise NotImplementedError(
            "DBConnector requires explicit query method. Use query() or incremental_query()"
        )

    def query(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        chunksize: int | None = None,
    ) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame.

        Args:
            sql: SQL query string.
            params: Optional query parameters (for parameterized queries).
            chunksize: If specified, return iterator of DataFrames.

        Returns:
            DataFrame containing query results.

        Raises:
            IngestionError: If query execution fails.
        """
        try:
            logger.info("executing_query", sql=sql[:100])

            df = pd.read_sql(
                sql,
                self.engine,
                params=params,
                chunksize=chunksize,
            )

            if chunksize is None:
                logger.info(
                    "query_complete",
                    rows=len(df),
                    columns=len(df.columns),
                )

            return df

        except Exception as e:
            logger.error("query_failed", sql=sql[:100], error=str(e))
            raise IngestionError(f"Database query failed: {e}") from e

    def incremental_query(
        self,
        table: str,
        watermark_column: str,
        last_watermark: Any | None = None,
        columns: list[str] | None = None,
        where_clause: str | None = None,
    ) -> pd.DataFrame:
        """Perform incremental query using watermark column.

        Args:
            table: Table name.
            watermark_column: Column to use for incremental loading (e.g., 'updated_at').
            last_watermark: Last watermark value (fetch records > this value).
                          If None, performs full load.
            columns: Optional list of columns to select.
            where_clause: Optional additional WHERE conditions.

        Returns:
            DataFrame containing incremental data.

        Raises:
            IngestionError: If query fails.
        """
        try:
            # Build SELECT clause
            select_cols = ", ".join(columns) if columns else "*"

            # Build WHERE clause
            where_parts = []
            if last_watermark is not None:
                # Format watermark based on type
                if isinstance(last_watermark, (datetime, str)):
                    watermark_str = f"'{last_watermark}'"
                else:
                    watermark_str = str(last_watermark)

                where_parts.append(f"{watermark_column} > {watermark_str}")

            if where_clause:
                where_parts.append(f"({where_clause})")

            where_sql = " AND ".join(where_parts) if where_parts else "1=1"

            # Build full query
            sql = f"SELECT {select_cols} FROM {table} WHERE {where_sql} ORDER BY {watermark_column}"

            logger.info(
                "incremental_query_started",
                table=table,
                watermark_column=watermark_column,
                last_watermark=last_watermark,
            )

            df = self.query(sql)

            # Get new watermark
            new_watermark = None
            if not df.empty and watermark_column in df.columns:
                new_watermark = df[watermark_column].max()

            logger.info(
                "incremental_query_complete",
                table=table,
                rows=len(df),
                new_watermark=new_watermark,
            )

            return df

        except Exception as e:
            logger.error(
                "incremental_query_failed",
                table=table,
                error=str(e),
            )
            raise IngestionError(f"Incremental query failed for {table}: {e}") from e

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        """Execute SQL statement (INSERT, UPDATE, DELETE, etc.).

        Args:
            sql: SQL statement.
            params: Optional query parameters.

        Raises:
            IngestionError: If execution fails.
        """
        try:
            logger.info("executing_statement", sql=sql[:100])

            with self.engine.begin() as conn:
                conn.execute(sql, params or {})

            logger.info("statement_complete")

        except Exception as e:
            logger.error("statement_failed", sql=sql[:100], error=str(e))
            raise IngestionError(f"SQL execution failed: {e}") from e

    def write_table(
        self,
        df: pd.DataFrame,
        table: str,
        if_exists: str = "append",
        index: bool = False,
        chunksize: int | None = None,
    ) -> None:
        """Write DataFrame to database table.

        Args:
            df: DataFrame to write.
            table: Target table name.
            if_exists: How to behave if table exists ('fail', 'replace', 'append').
            index: Whether to write DataFrame index.
            chunksize: Number of rows to write at a time.

        Raises:
            IngestionError: If write fails.
        """
        try:
            logger.info(
                "writing_table",
                table=table,
                rows=len(df),
                if_exists=if_exists,
            )

            df.to_sql(
                table,
                self.engine,
                if_exists=if_exists,
                index=index,
                chunksize=chunksize,
            )

            logger.info("table_write_complete", table=table)

        except Exception as e:
            logger.error("table_write_failed", table=table, error=str(e))
            raise IngestionError(f"Failed to write table {table}: {e}") from e
