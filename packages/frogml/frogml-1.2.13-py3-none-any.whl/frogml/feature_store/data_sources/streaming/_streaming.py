from abc import ABC

from frogml.feature_store.data_sources.base import BaseSource


class BaseStreamingSource(BaseSource, ABC):
    pass
