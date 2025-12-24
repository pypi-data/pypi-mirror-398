"""
Contains helpers for interacting with Skyramp test request.
"""

import inspect
import json
import textwrap
from typing import Callable, Optional, List
from skyramp.endpoint_base import _EndpointBase
from skyramp.rest_param import _RestParam as RestParam


class _Request:
    def __init__(
        self,
        name: str,
        endpoint_descriptor: _EndpointBase,
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
        self.name = name
        self.endpoint_descriptor = endpoint_descriptor
        if method_type is not None:
            self.method_type = method_type
        if params is not None:
            self.params = params
        if blob is not None:
            self.blob = blob
        if python_path is not None:
            self.python_path = python_path
        if python_function is not None:
            self.python_function = textwrap.dedent(inspect.getsource(python_function))
        if headers is not None:
            self.headers = headers
        if vars_ is not None:
            self.vars_ = vars_
        if method_name is not None:
            self.method_name = method_name
        if json_path is not None:
            self.json_path = json_path
        self.cookie_value = None
        self.vars_override = None
        self.blob_override = None
        self.blob_removal = None
        self.expected_code = expected_code
        self.unexpected_code = unexpected_code
        self.until = None

    def set_cookie_value(self, cookie_value: json):
        """
        Sets the cookie value for this step
        """
        self.cookie_value = cookie_value

    def override_vars(self, vars_: dict):
        """
        Sets the vars override for this step
        """
        self.vars_override = vars_

    def override_blob(self, blob: dict):
        """
        Sets the blob removal for this step
        """
        self.blob_override = blob

    def remove_blob(self, removal: List[str]):
        """
        Sets the blob override for this step
        """
        self.blob_removal = removal

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        return {"requestName": self.name}

    # pylint: disable=too-many-branches
    def as_request_dict(self, global_headers=None):
        """
        Convert the object to a JSON string.
        """
        # Determine method_name
        method_name = (
            self.method_name
            if hasattr(self, "method_name") and self.method_name is not None
            else (
                self.endpoint_descriptor.get_method_name_for_method_type(
                    self.method_type
                )
                if hasattr(self, "method_type") and self.method_type is not None
                else None
            )
        )
        request_dict = {
            "name": self.name,
            "endpointName": self.endpoint_descriptor.get_endpoint().get("name"),
            "methodName": method_name,
        }

        # Add headers if they exist
        if (
            global_headers is not None
            or hasattr(self, "headers")
            and self.headers is not None
        ):
            request_dict["headers"] = {}
        if global_headers is not None:
            request_dict["headers"] = global_headers
        if hasattr(self, "headers") and self.headers is not None:
            request_dict["headers"] = request_dict["headers"] | self.headers

        # Attributes to include in the response if they exist and are not None
        optional_attributes = [
            "vars_",
            "blob",
            "json_path",
            "python_path",
            "python_function",
            "params",
        ]
        for attr in optional_attributes:
            value = getattr(self, attr, None)
            key = attr
            if value is not None:
                key = key if attr != "python_function" else "python"
                key = key if attr != "vars_" else "vars"
                key = key if attr != "json_path" else "jsonPath"
                key = key if attr != "python_path" else "pythonPath"
                if attr == "params":
                    value = [param.to_json() for param in value]
                if attr == "blob":
                    value = json.dumps(json.loads(value, strict=False))
                request_dict[key] = value

        if self.expected_code != 0:
            request_dict["expectedCode"] = self.expected_code
        if self.unexpected_code != 0:
            request_dict["unexpectedCode"] = self.unexpected_code

        self._set_overrides(request_dict)

        return request_dict

    def _set_overrides(self, request_dict: dict):
        """
        Sets the override value for this step
        """
        if hasattr(self, "cookie_value") and self.cookie_value is not None:
            request_dict["cookies"] = self.cookie_value
        if hasattr(self, "vars_override") and self.vars_override is not None:
            request_dict["override"] = self.vars_override
        if hasattr(self, "blob_override") and self.blob_override is not None:
            request_dict["blobOverride"] = self.blob_override
        if hasattr(self, "blob_removal") and self.blob_removal is not None:
            request_dict["blobRemoval"] = self.blob_removal

    def get_async_value(self, json_path):
        """
        returns constructs for backend that accesses value using 
        jsonpath in response of this request
        """
        return f"res.{ json_path }"

    def get_async_code(self):
        """
        returns constructs for backend that accesses returned status code
        """
        return "code"
