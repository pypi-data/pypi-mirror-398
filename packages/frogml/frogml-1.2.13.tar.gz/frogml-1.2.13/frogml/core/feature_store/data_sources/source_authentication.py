from abc import ABC, abstractmethod

from pydantic import BaseModel

from frogml._proto.qwak.feature_store.sources.batch_pb2 import (
    AwsAssumeRoleAuthentication as ProtoAwsAssumeRoleAuthentication,
)
from frogml._proto.qwak.feature_store.sources.batch_pb2 import (
    AwsCredentialsAuthentication as ProtoAwsCredentialsAuthentication,
)


class AwsAuthentication(BaseModel, ABC):
    @abstractmethod
    def _to_proto(self):
        pass


class AwsAssumeRoleAuthentication(AwsAuthentication):
    role_arn: str

    def _to_proto(self) -> ProtoAwsAssumeRoleAuthentication:
        return ProtoAwsAssumeRoleAuthentication(role_arn=self.role_arn)


class AwsCredentialsAuthentication(AwsAuthentication):
    access_key_secret_name: str
    secret_key_secret_name: str

    def _to_proto(self) -> ProtoAwsCredentialsAuthentication:
        return ProtoAwsCredentialsAuthentication(
            access_key_secret_name=self.access_key_secret_name,
            secret_key_secret_name=self.secret_key_secret_name,
        )
