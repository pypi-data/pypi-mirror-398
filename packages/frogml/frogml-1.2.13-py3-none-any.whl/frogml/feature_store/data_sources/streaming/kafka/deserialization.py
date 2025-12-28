from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, Optional
from typing_extensions import Self

from pydantic import BaseModel, Field, PrivateAttr, model_validator

from frogml._proto.qwak.feature_store.sources.streaming_pb2 import (
    CustomDeserializer as ProtoCustomDeserializer,
)
from frogml._proto.qwak.feature_store.sources.streaming_pb2 import (
    Deserialization as ProtoDeserialization,
)
from frogml._proto.qwak.feature_store.sources.streaming_pb2 import (
    GenericDeserializer as ProtoGenericDeserializer,
)
from frogml._proto.qwak.feature_store.sources.streaming_pb2 import (
    MessageFormat as ProtoMessageFormat,
)
from frogml.core.exceptions import FrogmlException


class MessageFormat(Enum):
    JSON = ProtoMessageFormat.JSON
    AVRO = ProtoMessageFormat.AVRO


class Deserializer(BaseModel, ABC):
    @abstractmethod
    def _to_proto(self, artifact_path: Optional[str] = None) -> ProtoDeserialization:
        pass

    @abstractmethod
    def _get_function(self) -> Optional[Callable]:
        pass

    @classmethod
    def _from_proto(
        cls,
        proto_deserializer: ProtoDeserialization,
    ) -> Self:
        deserializer = getattr(
            proto_deserializer, proto_deserializer.WhichOneof("type")
        )

        if isinstance(deserializer, ProtoGenericDeserializer):
            return GenericDeserializer._from_proto(proto_deserializer=deserializer)
        elif isinstance(deserializer, ProtoCustomDeserializer):
            return CustomDeserializer._from_proto(proto_deserializer=deserializer)
        else:
            raise FrogmlException(f"Got unsupported deserializer type {deserializer}")


class GenericDeserializer(Deserializer):
    message_format: MessageFormat
    schema_name: str = Field(alias="schema", serialization_alias="schema")

    @property
    def schema(self) -> str:
        return self.schema_name

    def _to_proto(self, artifact_path: Optional[str] = None) -> ProtoDeserialization:
        # TODO: add backend schema validation
        return ProtoDeserialization(
            generic_deserializer=ProtoGenericDeserializer(
                deserializer_format=self.message_format.value, schema=self.schema_name
            )
        )

    def _get_function(self) -> Optional[Callable]:
        return None

    @classmethod
    def _from_proto(cls, proto_deserializer: ProtoGenericDeserializer) -> Self:
        return cls(
            message_format=MessageFormat(proto_deserializer.deserializer_format),
            schema=proto_deserializer.schema,
        )


class CustomDeserializer(Deserializer):
    function: Callable
    _artifact_path: Optional[str] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def __validate_custom_deserializer(self) -> Self:
        if self.function.__name__ == "<lambda>":
            raise FrogmlException("Custom Deserializer can not be set with a lambda")

        return self

    def _to_proto(self, artifact_path: Optional[str] = None) -> ProtoDeserialization:
        if artifact_path:
            self._artifact_path = artifact_path

        # TODO: add backend schema validation
        return ProtoDeserialization(
            custom_deserializer=ProtoCustomDeserializer(
                function_name=self.function.__name__, artifact_path=self._artifact_path
            )
        )

    @classmethod
    def _from_proto(cls, proto_deserializer: ProtoCustomDeserializer) -> Self:
        def dummy_deserializer(df):
            return df

        custom_function: Callable = dummy_deserializer
        custom_function.__name__ = proto_deserializer.function_name

        return cls(function=custom_function)

    def _get_function(self) -> Optional[Callable]:
        return self.function
