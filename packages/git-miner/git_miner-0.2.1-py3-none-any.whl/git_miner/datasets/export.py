from pathlib import Path
from typing import ClassVar, Literal

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .schemas import ContributorStatsSchema, RepositoryActivitySchema, RepositoryMetadataSchema


class DatasetExporter:
    """Export datasets to various formats."""

    SUPPORTED_FORMATS: ClassVar[list[Literal["csv", "json", "parquet"]]] = [
        "csv",
        "json",
        "parquet",
    ]

    def __init__(self, output_dir: str | Path = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _validate_format(self, format: str) -> Literal["csv", "json", "parquet"]:
        """Validate export format."""
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format}. Supported: {self.SUPPORTED_FORMATS}")
        return format

    def _export_csv(self, data: list[dict], filename: str):
        """Export data to CSV."""
        df = pd.DataFrame(data)
        output_path = self.output_dir / f"{filename}.csv"
        df.to_csv(output_path, index=False)
        print(f"Exported {len(data)} records to {output_path}")

    def _export_json(self, data: list[dict], filename: str):
        """Export data to JSON."""
        df = pd.DataFrame(data)
        output_path = self.output_dir / f"{filename}.json"
        df.to_json(output_path, orient="records", indent=2)
        print(f"Exported {len(data)} records to {output_path}")

    def _export_parquet(self, data: list[dict], filename: str):
        """Export data to Parquet."""
        df = pd.DataFrame(data)
        table = pa.Table.from_pandas(df)
        output_path = self.output_dir / f"{filename}.parquet"
        pq.write_table(table, output_path)
        print(f"Exported {len(data)} records to {output_path}")

    def export(
        self,
        data: list[dict],
        filename: str,
        format: Literal["csv", "json", "parquet"] = "csv",
    ):
        """Export dataset to specified format.

        Args:
            data: List of dictionary records
            filename: Output filename (without extension)
            format: Export format (csv, json, parquet)
        """
        format = self._validate_format(format)

        if not data:
            print(f"No data to export for {filename}")
            return

        if format == "csv":
            self._export_csv(data, filename)
        elif format == "json":
            self._export_json(data, filename)
        elif format == "parquet":
            self._export_parquet(data, filename)

    def export_dataset(
        self,
        dataset: dict[str, list[dict]],
        format: Literal["csv", "json", "parquet"] = "csv",
        prefix: str = "dataset",
    ):
        """Export a full dataset with multiple tables.

        Args:
            dataset: Dictionary with table names as keys and data lists as values
            format: Export format (csv, json, parquet)
            prefix: Filename prefix
        """
        format = self._validate_format(format)

        for table_name, data in dataset.items():
            if data:
                filename = f"{prefix}_{table_name}"
                self.export(data, filename, format)

    def export_repository_metadata(
        self, data: list[dict], filename: str = "repositories", format: str = "csv"
    ):
        """Export repository metadata dataset.

        Args:
            data: List of repository metadata dicts
            filename: Output filename
            format: Export format
        """
        format = self._validate_format(format)
        validated_data = [RepositoryMetadataSchema(**item).model_dump() for item in data]
        self.export(validated_data, filename, format)

    def export_activity_stats(
        self, data: list[dict], filename: str = "activities", format: str = "csv"
    ):
        """Export activity statistics dataset.

        Args:
            data: List of activity stats dicts
            filename: Output filename
            format: Export format
        """
        format = self._validate_format(format)
        validated_data = [RepositoryActivitySchema(**item).model_dump() for item in data]
        self.export(validated_data, filename, format)

    def export_contributor_stats(
        self, data: list[dict], filename: str = "contributors", format: str = "csv"
    ):
        """Export contributor statistics dataset.

        Args:
            data: List of contributor stats dicts
            filename: Output filename
            format: Export format
        """
        format = self._validate_format(format)
        validated_data = [ContributorStatsSchema(**item).model_dump() for item in data]
        self.export(validated_data, filename, format)
