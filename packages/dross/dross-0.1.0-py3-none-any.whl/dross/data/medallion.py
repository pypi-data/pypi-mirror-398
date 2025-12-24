"""Generalized medallion architecture for data pipelines.

Orchestrates Bronze (ingestion) → Silver (cleaning) → Gold (preparation)
using DuckDB and Unity Catalog.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Optional

import duckdb

logger = logging.getLogger(__name__)


class MedallionPipeline:
    """Generalized medallion architecture orchestrator."""

    def __init__(
        self,
        config: dict,
        uc_client: Optional[Any] = None,
        storage_base: Optional[Path] = None,
    ):
        """Initialize medallion pipeline.

        Args:
            config: Unity Catalog configuration dict with keys:
                - project_name: UC catalog name
                - schema: dict with bronze, silver, gold keys
                - storage_base: base path for parquet storage
            uc_client: UC client instance (dross.tracking.UCClient)
            storage_base: Base storage path for medallion layers

        """
        self.config = config
        self.uc = uc_client
        self.storage_base = storage_base or Path(
            config.get("storage_base", "").replace("file://", "")
        )
        self.catalog = config.get("project_name", "kaggle")
        self.schemas = config.get("schema", {})

    async def ingest(
        self,
        source_file: Path,
        catalog: Optional[str] = None,
        schema_name: Optional[str] = None,
        table_name: Optional[str] = None,
        columns: Optional[list] = None,
    ) -> None:
        """Ingest raw CSV to Bronze layer.

        Args:
            source_file: Path to source CSV
            catalog: UC catalog name (uses self.catalog if not provided)
            schema_name: UC schema name (uses bronze if not provided)
            table_name: UC table name
            columns: Column definitions for UC registration

        """
        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            return

        catalog = catalog or self.catalog
        schema_name = schema_name or self.schemas.get("bronze", "bronze")
        table_name = table_name or "raw"

        # Setup storage
        table_storage = self.storage_base / "bronze" / table_name
        table_storage.mkdir(parents=True, exist_ok=True)
        parquet_file = table_storage / "data.parquet"

        logger.info(f"Ingesting {source_file} to UC {catalog}.{schema_name}.{table_name}")

        # Ingest using DuckDB
        conn = duckdb.connect()
        conn.execute(
            f"COPY (SELECT * FROM read_csv_auto('{source_file}')) "
            f"TO '{parquet_file}' (FORMAT PARQUET)"
        )
        logger.info(f"Parquet written to {parquet_file}")

        # Register in UC if client provided
        if self.uc:
            await self.uc.catalog_create(catalog)
            await self.uc.schema_create(catalog, schema_name)
            if columns:
                await self.uc.table_create(
                    catalog, schema_name, table_name, columns, f"file://{table_storage}"
                )
                logger.info(f"Registered UC table: {catalog}.{schema_name}.{table_name}")

    async def clean(
        self,
        source_table: str,
        target_table: str,
        transform_func: Callable,
        catalog: Optional[str] = None,
        source_schema: Optional[str] = None,
        target_schema: Optional[str] = None,
        columns: Optional[list] = None,
    ) -> None:
        """Transform and clean data: Bronze → Silver.

        Args:
            source_table: Source table name
            target_table: Target table name
            transform_func: Function that takes source parquet path, returns query
            catalog: UC catalog name
            source_schema: Source schema (bronze)
            target_schema: Target schema (silver)
            columns: Column definitions for UC registration

        """
        catalog = catalog or self.catalog
        source_schema = source_schema or self.schemas.get("bronze", "bronze")
        target_schema = target_schema or self.schemas.get("silver", "silver")

        # Source path
        source_storage = self.storage_base / "bronze" / source_table / "data.parquet"
        if not source_storage.exists():
            logger.error(f"Source data not found at {source_storage}")
            return

        # Target storage
        target_storage = self.storage_base / "silver" / target_table
        target_storage.mkdir(parents=True, exist_ok=True)
        target_parquet = target_storage / "data.parquet"

        logger.info(f"Cleaning {source_table} → {target_table}")

        # Apply transform function
        conn = duckdb.connect()
        query = transform_func(str(source_storage))
        conn.execute(f"COPY ({query}) TO '{target_parquet}' (FORMAT PARQUET)")
        logger.info(f"Silver data written to {target_parquet}")

        # Register in UC
        if self.uc:
            await self.uc.schema_create(catalog, target_schema)
            if columns:
                await self.uc.table_create(
                    catalog, target_schema, target_table, columns, f"file://{target_storage}"
                )
                logger.info(f"Registered UC table: {catalog}.{target_schema}.{target_table}")

    async def prepare(
        self,
        source_table: str,
        target_table: str,
        catalog: Optional[str] = None,
        source_schema: Optional[str] = None,
        target_schema: Optional[str] = None,
        columns: Optional[list] = None,
    ) -> None:
        """Prepare final dataset: Silver → Gold.

        Args:
            source_table: Source table name
            target_table: Target table name
            catalog: UC catalog name
            source_schema: Source schema (silver)
            target_schema: Target schema (gold)
            columns: Column definitions for UC registration

        """
        import shutil

        catalog = catalog or self.catalog
        source_schema = source_schema or self.schemas.get("silver", "silver")
        target_schema = target_schema or self.schemas.get("gold", "gold")

        # Source path
        source_storage = self.storage_base / "silver" / source_table / "data.parquet"
        if not source_storage.exists():
            logger.error(f"Source data not found at {source_storage}")
            return

        # Target storage
        target_storage = self.storage_base / "gold" / target_table
        target_storage.mkdir(parents=True, exist_ok=True)
        target_parquet = target_storage / "data.parquet"

        logger.info(f"Preparing {source_table} → {target_table}")

        # Copy to gold
        shutil.copy2(source_storage, target_parquet)
        logger.info(f"Gold dataset ready at {target_parquet}")

        # Register in UC
        if self.uc:
            await self.uc.schema_create(catalog, target_schema)
            if columns:
                await self.uc.table_create(
                    catalog, target_schema, target_table, columns, f"file://{target_storage}"
                )
                logger.info(f"Registered UC table: {catalog}.{target_schema}.{target_table}")
