"""Schema validator for validating DataFrames against Pydantic schemas.

This module provides utilities to validate pandas DataFrames against strict schema definitions,
with support for Dead Letter Queue (DLQ) for invalid records.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import structlog
from pydantic import ValidationError as PydanticValidationError

from forge_flow.exceptions import ValidationError
from forge_flow.schemas.base import StrictSchema

logger = structlog.get_logger(__name__)


class SchemaValidator:
    """Validates DataFrames against Pydantic schemas.

    This class enforces data contracts by validating each row of a DataFrame
    against a Pydantic schema. Invalid records can be logged to a Dead Letter Queue.

    Example:
        >>> from pydantic import Field
        >>> class UserSchema(StrictSchema):
        ...     user_id: int = Field(gt=0)
        ...     age: int = Field(ge=0, le=120)
        ...     email: str
        ...
        >>> validator = SchemaValidator(UserSchema)
        >>> df = pd.DataFrame({
        ...     'user_id': [1, 2, -3],
        ...     'age': [25, 30, 150],
        ...     'email': ['a@b.com', 'c@d.com', 'invalid']
        ... })
        >>> clean_df = validator.validate(df, raise_on_error=False)
        >>> # clean_df contains only valid rows (first two)
    """

    def __init__(
        self,
        schema: type[StrictSchema],
        dlq_path: Path | None = None,
    ) -> None:
        """Initialize the schema validator.

        Args:
            schema: Pydantic schema class to validate against.
            dlq_path: Optional path to write invalid records (Dead Letter Queue).
                     If None, invalid records are only logged.
        """
        self.schema = schema
        self.dlq_path = dlq_path
        self._validation_count = 0
        self._error_count = 0

    def validate(
        self,
        df: pd.DataFrame,
        raise_on_error: bool = True,
    ) -> pd.DataFrame:
        """Validate DataFrame against schema.

        Args:
            df: DataFrame to validate.
            raise_on_error: If True, raise ValidationError on first invalid record.
                          If False, filter out invalid records and continue.

        Returns:
            DataFrame containing only valid records.

        Raises:
            ValidationError: If raise_on_error=True and validation fails.
        """
        if df.empty:
            logger.warning("validate_empty_dataframe", schema=self.schema.__name__)
            return df

        valid_rows: list[dict[str, Any]] = []
        invalid_rows: list[dict[str, Any]] = []

        for idx, row in df.iterrows():
            try:
                # Validate row against schema
                validated = self.schema.model_validate(row.to_dict())
                valid_rows.append(validated.to_dict())
                self._validation_count += 1

            except PydanticValidationError as e:
                self._error_count += 1
                error_detail = {
                    "row_index": idx,
                    "errors": e.errors(),
                    "data": row.to_dict(),
                }

                logger.error(
                    "validation_failed",
                    schema=self.schema.__name__,
                    row_index=idx,
                    error_count=len(e.errors()),
                )

                invalid_rows.append(error_detail)

                if raise_on_error:
                    raise ValidationError(f"Validation failed for row {idx}: {e.errors()}") from e

        # Handle invalid records
        if invalid_rows:
            self._handle_invalid_records(invalid_rows)

        # Create DataFrame from valid rows
        if not valid_rows:
            logger.warning(
                "no_valid_records",
                schema=self.schema.__name__,
                total_rows=len(df),
                invalid_rows=len(invalid_rows),
            )
            return pd.DataFrame()

        valid_df = pd.DataFrame(valid_rows)

        logger.info(
            "validation_complete",
            schema=self.schema.__name__,
            total_rows=len(df),
            valid_rows=len(valid_rows),
            invalid_rows=len(invalid_rows),
        )

        return valid_df

    def _handle_invalid_records(self, invalid_rows: list[dict[str, Any]]) -> None:
        """Handle invalid records by writing to DLQ if configured.

        Args:
            invalid_rows: List of invalid record details.
        """
        if not self.dlq_path:
            return

        try:
            # Ensure DLQ directory exists
            self.dlq_path.parent.mkdir(parents=True, exist_ok=True)

            # Append invalid records to DLQ file
            dlq_df = pd.DataFrame(invalid_rows)
            mode = "a" if self.dlq_path.exists() else "w"
            header = not self.dlq_path.exists()

            dlq_df.to_csv(self.dlq_path, mode=mode, header=header, index=False)

            logger.info(
                "dlq_written",
                dlq_path=str(self.dlq_path),
                invalid_count=len(invalid_rows),
            )

        except Exception as e:
            logger.error(
                "dlq_write_failed",
                dlq_path=str(self.dlq_path),
                error=str(e),
            )

    def get_stats(self) -> dict[str, int]:
        """Get validation statistics.

        Returns:
            Dictionary with validation and error counts.
        """
        return {
            "validation_count": self._validation_count,
            "error_count": self._error_count,
        }

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_count = 0
        self._error_count = 0
