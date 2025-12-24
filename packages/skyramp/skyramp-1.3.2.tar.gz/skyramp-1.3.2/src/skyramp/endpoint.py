"""
Contains helpers for interacting with Skyramp endpoints.
"""

import os
import ctypes
import json
from typing import Optional, Callable
import yaml
from skyramp.endpoint_base import _EndpointBase
from skyramp.test_request import _Request
from skyramp.rest_param import _RestParam as RestParam

from skyramp.utils import _library, _call_function, SKYRAMP_YAML_VERSION

ARGUMENT_TYPE = [
    ctypes.c_char_p,
    ctypes.c_char_p,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_char_p,
]

class _Endpoint(_EndpointBase):
    """
    Base class for endpoints. This should not be used for instantiation.
    """

    # pylint: disable=too-many-branches
    def __init__(
        self, endpoint_data: str, endpoint_address: str = None, rest_path: str = "",
    ) -> None:
        try:
            endpoint = json.loads(endpoint_data)
            self.services = endpoint["services"]
            if endpoint_address is not None:
                if "services" in endpoint and isinstance(endpoint["services"], list):
                    # Iterate over the list to find and update the 'addr' value for each service
                    for svc in self.services:
                        svc["addr"] = endpoint_address
                        del svc["alias"]

            # If rest_path is provided, we need to find the endpoint with the matching path
            if rest_path != "":
                for endpoint in endpoint["endpoints"]:
                    if endpoint["path"] == rest_path:
                        self.endpoint = endpoint
                        break
            elif len(endpoint["endpoints"]) > 0:
                self.endpoint = endpoint["endpoints"][0]
            if "responses" in endpoint:
                self.responses = endpoint["responses"]

            self.mock_description = {
                "version": SKYRAMP_YAML_VERSION,
                "services": self.services,
                "endpoints": [self.endpoint],
            }
            if "responses" in endpoint:
                self.mock_description["responses"] = self.responses
        except Exception as ex:
            raise Exception(f"failed to parse endpoint data: {ex}")

    def get_endpoint(self):
        return self.endpoint

    def mock_method(
        self, method_name: str, mock_object: str, dynamic: bool = False
    ) -> None:
        """
        Adds the given mock_data blob to the method name for this endpoint.
        """
        if method_name not in [
            method.get("name") for method in self.endpoint["methods"]
        ]:
            raise Exception(f"method {method_name} not found")

        for response in self.responses:
            if response.get("methodName") == method_name and response.get(
                "endpointName"
            ) == self.endpoint.get("name"):
                # Overwrite this response
                if dynamic:
                    response["javascriptPath"] = mock_object
                    response.pop("blob", None)
                else:
                    response["blob"] = mock_object["responseValue"]["blob"]
                    response.pop("javascriptPath", None)
                return

        # If a response was not found, create a new one
        new_response = {
            "methodName": method_name,
            "endpointName": self.endpoint.get("name"),
        }

        if dynamic:
            new_response["javascriptPath"] = mock_object
        else:
            new_response["blob"] = mock_object["responseValue"]["blob"]

        self.responses.append(new_response)

    def mock_method_from_file(self, method_name: str, file_name: str) -> None:
        """
        Uses the given mock data from a provided file, and associates it with the
        corresponding method_name for this endpoint.

        Args:
            file_name: The name of the file containing the mock data.
            method_name: The name of the method to associate with the mock data.
        """
        _, file_ext = os.path.splitext(file_name)

        try:
            with open(file_name) as file:
                file_contents = file.read()
        except:
            raise Exception(f"failed to open file: {file_name}")

        dynamic = False

        if file_ext == ".json":
            data = json.loads(file_contents)
        elif file_ext in [".yaml", ".yml"]:
            data = yaml.safe_load(file_contents)
        elif file_ext == ".js":
            dynamic = True
            data = file_name
        else:
            raise Exception(
                f"unsupported file format: {file_ext}. Only JSON, YAML, and JS are supported"
            )

        return self.mock_method(
            method_name=method_name, mock_object=data, dynamic=dynamic
        )

    def write_mock_configuration_to_file(self, alias: str) -> None:
        """
        Persists (as a file to be used by Skyramp) all of the mock configurations
        for this endpoint.

        Args:
            alias: The name of the networking alias that will be used to reach this endpoint.
        For example, it can be the Kubernetes service name or the Docker alias name.
        """
        try:
            yaml_content = yaml.dump(self.mock_description)
        except:
            raise Exception("failed to convert mock description to YAML")

        func = _library.writeMockDescriptionWrapper
        argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        restype = ctypes.c_char_p

        _call_function(func, argtypes, restype, [yaml_content.encode(), alias.encode()])

    def get_method_name_for_method_type(self, method_type: str) -> str:
        """
        Returns the method name for the given method type.

        Args:
            method_type: The type of method to get the name for.

        Returns:
            The name of the method.
        """
        for method in self.endpoint.get("methods"):
            if method.get("type").lower() == method_type.lower():
                return method["name"]
        methods = self.endpoint.get("methods")
        raise Exception(f"method type {method_type} not found. Methods: {methods}")

    def new_request(self,
        name: str,
        method_type: Optional[str] = None,
        method_name: Optional[str] = None,
        params: Optional[RestParam] = None,
        blob: Optional[str] = None,
        headers: Optional[dict] = None,
        vars_: Optional[dict] = None,
        python_path: Optional[str] = None,
        python_function: Optional[Callable] = None,
        json_path: Optional[str] = None,
        expected_code: Optional[int] = 0,
        unexpected_code: Optional[int] = 0,
    ) -> None:
        """
        Creates a new Request that is associated with this Endpoint
        """
        return _Request(
            name,
            self,
            method_type,
            method_name,
            params,
            blob,
            headers,
            vars_,
            python_path,
            python_function,
            json_path,
            expected_code,
            unexpected_code
        )

class _GrpcEndpoint(_Endpoint):
    """
    Represents an endpoint of a gRPC based service.
    """

    def __init__(
        self,
        name: str,
        service: str,
        port: int,
        pb_file: str,
        endpoint_address: str = None,
        alias: Optional[str] = None,
    ) -> None:
        """
        GrpcEndpoint constructor.

        Args:
            name: Name of the endpoint
            service: The service name to associate with this endpoint
            port: Port number where the endpoint will be reached
            pb_file: Protobuf file with definitions corresponding to this endpoint
            endpoint_address: (optional) Docker endpoint address to use for this endpoint
        """
        func = _library.newGrpcEndpointWrapper
        argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
        restype = ctypes.c_char_p

        svc_name = name
        if alias is not None and alias != "":
            svc_name = alias

        output = _call_function(
            func,
            argtypes,
            restype,
            [svc_name.encode(), service.encode(), port, pb_file.encode()],
            True,
        )

        super().__init__(output, endpoint_address, "")


class _RestEndpoint(_Endpoint):
    """
    Represents an endpoint of a REST based service.
    """

    def __init__(
        self,
        name: str = "",
        openapi_tag: str = "",
        port: int = 0,
        openapi_file: str = "",
        service_name: str = "",
        rest_path: str = "",
        endpoint_address: str = None,
        alias: Optional[str] = None,
    ) -> None:
        """
        RestEndpoint constructor.

        Args:
            name: name of the endpoint
            openapi_tag: (optional) tag to filter an OpenAPI file
            port: Port number where the endpoint will be reached
            openapi_file: (optional) OpenAPI file with definitions corresponding to this endpoint
            service_name: (optional) name of the service to use for this endpoint
            rest_path: (optional) path to use for this endpoint
            endpoint_address: (optional) Docker endpoint to use for this endpoint
        """
        self.service_name = service_name
        self.port = port
        self.rest_path = rest_path
        # call some function

        if self.service_name != "":
            func = _library.getEndpointWrapper
            argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
            restype = ctypes.c_char_p

            output = _call_function(
                func,
                argtypes,
                restype,
                [service_name.encode(), port, rest_path.encode()],
                True,
            )
        else:
            func = _library.newRestEndpointWrapper
            restype = ctypes.c_char_p

            svc_name = name
            if alias is not None and alias != "":
                svc_name = alias

            output = _call_function(
                func,
                ARGUMENT_TYPE,
                restype,
                [
                    svc_name.encode(),
                    openapi_tag.encode(),
                    port,
                    openapi_file.encode(),
                    rest_path.encode(),
                ],
                True,
            )

        super().__init__(output, endpoint_address, rest_path)
