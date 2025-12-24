"""Unity Catalog client wrapper."""

import logging

from unitycatalog import client

logger = logging.getLogger(__name__)


class UCClient:
    """Unity Catalog Python SDK client wrapper."""

    def __init__(
        self, server: str = "http://localhost:8080", auth_token: str | None = None
    ) -> None:
        """Initialize the Unity Catalog client.

        Args:
            server: URL of the Unity Catalog server
            auth_token: Optional authentication token

        """
        config = client.Configuration()
        config.host = f"{server}/api/2.1/unity-catalog"
        if auth_token:
            config.api_key["api_key"] = auth_token

        self.api_client = client.ApiClient(config)
        self.catalogs_api = client.CatalogsApi(self.api_client)
        self.schemas_api = client.SchemasApi(self.api_client)
        self.tables_api = client.TablesApi(self.api_client)

    async def close(self) -> None:
        """Close the underlying API client."""
        await self.api_client.close()

    async def catalog_create(self, name: str) -> None:
        """Create a new catalog if it doesn't exist."""
        try:
            await self.catalogs_api.get_catalog(name)
        except Exception:
            try:
                await self.catalogs_api.create_catalog(client.CreateCatalog(name=name))
                logger.info(f"Created catalog: {name}")
            except Exception as e:
                logger.error(f"Failed to create catalog {name}: {e}")

    async def schema_create(self, catalog: str, name: str) -> None:
        """Create a new schema within a catalog if it doesn't exist."""
        full_name = f"{catalog}.{name}"
        try:
            await self.schemas_api.get_schema(full_name)
        except Exception:
            try:
                await self.schemas_api.create_schema(
                    client.CreateSchema(name=name, catalog_name=catalog)
                )
                logger.info(f"Created schema: {full_name}")
            except Exception as e:
                logger.error(f"Failed to create schema {full_name}: {e}")

    async def table_create(
        self, catalog: str, schema: str, name: str, columns: list, storage_location: str
    ) -> None:
        """Create an external table within a schema if it doesn't exist."""
        full_name = f"{catalog}.{schema}.{name}"
        try:
            await self.tables_api.get_table(full_name)
        except Exception:
            try:
                # Basic column creation for UC
                uc_columns = [
                    client.ColumnInfo(
                        name=c["name"],
                        type_name=getattr(client.ColumnTypeName, c["type"].upper()),
                        type_text=c["type"].lower(),
                        type_json=f'{{ "type": "{c["type"].lower()}" }}',
                        position=i,
                        nullable=True,
                    )
                    for i, c in enumerate(columns)
                ]
                create_table_req = client.CreateTable(
                    name=name,
                    catalog_name=catalog,
                    schema_name=schema,
                    table_type=client.TableType.EXTERNAL,
                    storage_location=storage_location,
                    data_source_format=client.DataSourceFormat.DELTA,
                    columns=uc_columns,
                )
                await self.tables_api.create_table(create_table_req)
                logger.info(f"Created table: {full_name}")
            except Exception as e:
                logger.error(f"Failed to create table {full_name}: {e}")
