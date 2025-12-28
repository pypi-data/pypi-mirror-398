from typing import Optional
from typing_extensions import Self

from pydantic import Field, model_validator

from frogml._proto.qwak.feature_store.sources.batch_pb2 import (
    BatchSource as ProtoBatchSource,
    CatalogSource as ProtoCatalogSource,
    UnityCatalogSource as ProtoUnityCatalogSource,
)
from frogml._proto.qwak.feature_store.sources.data_source_pb2 import (
    DataSourceSpec as ProtoDataSourceSpec,
)
from frogml.core.exceptions import FrogmlException
from frogml.feature_store.data_sources.batch._batch import BaseBatchSource

RESERVED_CATALOG_NAME = "qwak_catalog"


class UnityCatalogSource(BaseBatchSource):
    """Unity Catalog batch data source.

    Attributes:
        uri (str): Connection uri to Unity Catalog i.e https://<workspace-instance-name>.<domain-name>/api/2.1/unity-catalog

        schema (str): The Unity Catalog schema name where the data is located.

        catalog (str): The Unity Catalog catalog name.

        personal_access_token_secret_name (Optional[str]): The name of the secret
            containing the personal access token for authentication. e.g "my-pat-secret"

        table (Optional[str]): The table name within the specified catalog and schema.
            Either 'table' or 'query' must be provided, but not both. e.g "my_table"

        query (Optional[str]): A SQL query to execute against the Unity Catalog.
            Either 'query' or 'table' must be provided, but not both. e.g "select * from {catalog}.{schema}.{table}"

        repository (Optional[str]): The data source group.

    """

    uri: str
    schema_name: str = Field(alias="schema", serialization_alias="schema")
    catalog: str
    personal_access_token_secret_name: Optional[str] = None
    table: Optional[str] = None
    query: Optional[str] = None

    @property
    def schema(self) -> str:
        return self.schema_name

    @model_validator(mode="after")
    def __validate_unity_catalog(self) -> Self:
        if not self.uri:
            raise FrogmlException("`uri` cannot be empty.")

        if not self.schema_name:
            raise FrogmlException("`schema` cannot be empty.")

        if not self.catalog:
            raise FrogmlException("`catalog` cannot be empty.")

        if not self.personal_access_token_secret_name:
            raise FrogmlException(
                "`personal_access_token_secret_name` cannot be empty."
            )

        if self.catalog == RESERVED_CATALOG_NAME:
            raise FrogmlException(
                f"`catalog` can not be set to `{RESERVED_CATALOG_NAME}`.",
            )

        if bool(self.query) == bool(self.table):
            raise FrogmlException("Either `query` or `table` must be provided.")

        return self

    def _to_proto(self, artifact_url: Optional[str] = None) -> ProtoDataSourceSpec:
        return ProtoDataSourceSpec(
            data_source_repository_name=self.repository,
            batch_source=ProtoBatchSource(
                name=self.name,
                description=self.description,
                date_created_column=self.date_created_column,
                catalogSource=ProtoCatalogSource(
                    url=self.uri,
                    query=self.query,
                    table=self.table,
                    unityCatalogSource=ProtoUnityCatalogSource(
                        catalog=self.catalog,
                        schema=self.schema_name,
                        personal_access_token_secret_name=self.personal_access_token_secret_name,
                    ),
                ),
            ),
        )

    @classmethod
    def _from_proto(cls, proto: ProtoBatchSource) -> Self:
        catalog_source = proto.catalogSource
        return cls(
            name=proto.name,
            date_created_column=proto.date_created_column,
            description=proto.description,
            uri=catalog_source.url,
            schema=catalog_source.unityCatalogSource.schema,
            catalog=catalog_source.unityCatalogSource.catalog,
            personal_access_token_secret_name=catalog_source.unityCatalogSource.personal_access_token_secret_name,
            table=catalog_source.table,
            query=catalog_source.query,
        )
