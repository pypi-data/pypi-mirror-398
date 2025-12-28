import grpc
from typing_extensions import Self

from frogml.core.inner.const import FrogMLConstants
from frogml.core.inner.tool.auth import FrogMLAuthClient


class FrogMLAuthMetadataPlugin(grpc.AuthMetadataPlugin):
    def __init__(self: Self, should_pass_jf_tenant_id: bool = True):
        self.__auth_client = FrogMLAuthClient()
        self.__should_pass_jf_tenant_id: bool = should_pass_jf_tenant_id

    def __call__(
        self,
        context: grpc.AuthMetadataContext,
        callback: grpc.AuthMetadataPluginCallback,
    ):
        """Implements authentication by passing metadata to a callback.

        Args:
            context: An AuthMetadataContext providing information on the RPC that
                the plugin is being called to authenticate.
            callback: A callback that accepts a sequence of metadata key/value pairs and a None
                parameter.
        """
        token: str = self.__auth_client.get_token()
        metadata: list[tuple[str, str]] = [
            (FrogMLConstants.SIGNATURE_HEADER_KEY, f"Bearer {token}")
        ]

        if self.__should_pass_jf_tenant_id:
            jfrog_tenant_id: str = self.__auth_client.get_tenant_id()
            metadata.append(
                (FrogMLConstants.JFROG_TENANT_HEADER_KEY.lower(), jfrog_tenant_id)
            )

        callback(metadata, None)

    @property
    def should_pass_jf_tenant_id(self: Self) -> bool:
        return self.__should_pass_jf_tenant_id
