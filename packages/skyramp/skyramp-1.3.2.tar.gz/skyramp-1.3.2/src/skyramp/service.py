"""
Contains helpers for interacting with Skyramp service.
"""

from typing import Optional

from skyramp.endpoint import _RestEndpoint, _GrpcEndpoint


class _Service:
    def __init__(self,
             name,
             addr: Optional[str] = None,
             port: Optional[int] = 0,
             alias: Optional[str] = None,
             secure: Optional[bool] = None,
             protocol: Optional[str] = None,
             credentails: Optional[str] = None,
        ) -> None:
        self.name = name
        self.addr = addr
        self.port = port
        self.alias = alias
        self.secure = secure
        self.protocol = protocol
        self.credential = credentails

    def new_rest_endpoint(
        self,
        name: str,
        rest_path: str,
        openapi_tag: str = "",
        openapi_file: str = "",
        ) -> _RestEndpoint:
        """
        Creates a new REST endpoint that is associated with this Service
        """
        return _RestEndpoint(
            name,
            openapi_tag,
            self.port,
            openapi_file,
            "",
            rest_path,
            self.addr,
            self.alias
        )

    def new_grpc_endpoint(
        self,
        name: str,
        pb_file: str,
        ) -> None:
        """
        Creates a new gRPC endpoint that is associated with this Service
        """
        return _GrpcEndpoint(
            name,
            self.name,
            self.port,
            pb_file,
            self.addr,
            self.alias
        )

    def to_json(self):
        """
        Convert the service object to json data.
        """
        attributes = ["name", "addr", "alias", "secure", "protocol", "credential"]
        json_data = {
            attr: getattr(self, attr)
            for attr in attributes
            if getattr(self, attr) is not None
        }
        return json_data
