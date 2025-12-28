from typing_extensions import Self
from pydantic import BaseModel, Field

from frogml._proto.qwak.feature_store.sources.data_source_attribute_pb2 import (
    DataSourceAttributes as ProtoDataSourceAttributes,
)
from frogml.core.feature_store._common.source_code_spec import SourceCodeSpec


class DataSourceAttributes(BaseModel):
    source_code_spec: SourceCodeSpec = Field(default_factory=SourceCodeSpec)

    def _to_proto(self) -> ProtoDataSourceAttributes:
        return ProtoDataSourceAttributes(
            source_code_spec=self.source_code_spec._to_proto()
        )

    @classmethod
    def _from_proto(cls, proto: ProtoDataSourceAttributes) -> Self:
        return cls(
            source_code_spec=SourceCodeSpec._from_proto(proto=proto.source_code_spec)
        )
