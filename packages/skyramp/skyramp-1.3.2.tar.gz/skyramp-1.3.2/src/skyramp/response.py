"""
Contains helpers for interacting with Skyramp mock response.
"""
import inspect
import textwrap
import json
from typing import Callable, Dict, List, Union, Optional

from skyramp.endpoint import _Endpoint
from skyramp.rest_param import _RestParam

class _ResponseValue:
    """
    Represents a response value.
    """
    def __init__(self,
                 name: str,
                 endpoint_descriptor: _Endpoint,
                 method_type: Optional[str]=None,
                 method_name: Optional[str]=None,
                 content_type: Optional[str]=None,
                 blob: Optional[Union[Dict, str]] = None,
                 blob_override: Optional[Dict] = None,
                 python_function: Optional[Callable] = None,
                 python_path: Optional[str] = None,
                 params: Optional[List[_RestParam]] = None,
                 status_code: Optional[int] = None,
                 headers: Optional[Dict] = None):
        """
        Create a new ResponseValue instance.

        Args:
            content_type (str, optional): The content type.
            blob (Dict, optional): The response body as a JSON object.
            blob_override (Dict, optional): Json blob overrides.
            method_type (str, optional): The method type.
            method_name (str, optional): The method name.
            python_function (Callable, optional): The Python response as a function.
            python_path (str, optional): The path to a Python file.
            params (List[_RestParam], optional): An array of REST parameters.
            status_code (int, optional): Status code
            headers (Dict, optional): A dictionary of key-value pairs for headers.
        """
        self.name = name
        self.endpoint_descriptor = endpoint_descriptor
        if method_type is not None:
            self.method_type = method_type
        if method_name is not None:
            self.method_name = method_name
        if content_type is not None:
            self.content_type = content_type
        if blob is not None:
            self.blob = blob
        if blob_override is not None:
            self.blob_override = blob_override
        if python_function is not None:
            self.python_function = textwrap.dedent(inspect.getsource(python_function))
            func_name = python_function.__name__
            if func_name != "handler":
                self.func_name= func_name
        if python_path is not None:
            self.python_path = python_path
        if params is not None:
            self.params = params
        if headers is not None:
            self.headers = headers
        self.traffic_config = None
        self.proxy_live_service = False
        self.response_value = None
        self.cookie_value = None
        self.status_code = status_code

    def set_traffic_config(self, traffic_config):
        """ Set the traffic config. """
        self.traffic_config = traffic_config

    def enable_proxy_live_service(self):
        """ Enable proxy live service. """
        self.proxy_live_service = True

    def set_value(self, response_value: json):
        """
        Sets the response value for this step
        """
        self.response_value = response_value

    def set_cookie_value(self, cookie_value: json):
        """
        Sets the cookie value for this step
        """
        self.cookie_value = cookie_value

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        # Determine method_name
        method_name = (
            self.method_name
            if hasattr(self, 'method_name') and self.method_name is not None
            else self.endpoint_descriptor.get_method_name_for_method_type(self.method_type)
            if hasattr(self, 'method_type') and self.method_type is not None
            else None
        )

        response = {
            "name": self.name,
            "endpointName": self.endpoint_descriptor.endpoint.get("name"),
            "methodName": method_name,
        }

        # Attributes to include in the response if they exist and are not None
        optional_attributes = [
            "content_type", "blob", "blob_override", 
            "python_path", "python_function", "params", "headers", "status_code", "func_name",
        ]

        for attr in optional_attributes:
            value = getattr(self, attr, None)
            if value is not None:
                key = attr if attr != "blob_override" else "blobOverride"
                key = key if attr != "python_function" else "python"
                key = key if attr != "content_type" else "contentType"
                key = key if attr != "python_path" else "pythonPath"
                key = key if attr != "status_code" else "statusCode"
                key = key if attr != "func_name" else "funcName"
                if attr == "params":
                    value = [param.to_json() for param in value]
                response[key] = value

        return response
