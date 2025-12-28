from abc import ABC, abstractmethod

from pydantic import BaseModel


class FileSystemConfiguration(BaseModel, ABC):
    @abstractmethod
    def _to_proto(self):
        pass

    @abstractmethod
    def _from_proto(self, proto):
        pass
