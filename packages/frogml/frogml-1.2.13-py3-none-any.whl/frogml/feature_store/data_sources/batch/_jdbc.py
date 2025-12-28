from abc import ABC
from typing import Optional
from typing_extensions import Self
from pydantic import model_validator

from frogml.core.exceptions import FrogmlException
from frogml.feature_store.data_sources.batch._batch import BaseBatchSource


class JdbcSource(BaseBatchSource, ABC):
    username_secret_name: Optional[str] = None
    password_secret_name: Optional[str] = None
    url: Optional[str] = None
    db_table: Optional[str] = None
    query: Optional[str] = None

    @model_validator(mode="after")
    def __validate_jdbc(self) -> Self:
        if not (bool(self.db_table) ^ bool(self.query)):
            raise FrogmlException("Only one of query and db_table must be set")

        return self
