from abc import ABC
from frogml.feature_store.data_sources.base import BaseSource


class BaseBatchSource(BaseSource, ABC):
    date_created_column: str
