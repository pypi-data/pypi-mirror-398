from typing import Union
from urllib.parse import ParseResult

from frogml.core.exceptions import FrogmlException


class FrogmlGrpcAddressException(FrogmlException):
    def __init__(self, details: str, grpc_address: Union[str, ParseResult]):
        self.message = f"Not a valid gRPC address: '{grpc_address}'. Details: {details}"
