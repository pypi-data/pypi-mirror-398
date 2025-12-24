"""
This module provides the ResponseV2 class for handling HTTP response data in the Skyramp framework.
It includes functionality for converting response data to dictionary format 
and handling JSON body content.
"""

import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
@dataclass
class RequestV2:
    """
    Represents an HTTP request with configurable parameters 
    for URL, headers, body, and various overrides.
    Provides methods for JSON serialization and dictionary conversion.
    """
    name: Optional[str] = None
    _vars_data: Optional[Dict[str, Any]] =None
    test_id: Optional[str] = field(
        default=None,
        metadata={"description": "test group ID"}
    )
    url: Optional[str] = field(
        default=None,
        metadata={"description": "URL e.g., http://example.com"}
    )
    path: Optional[str] = field(
        default=None,
        metadata={"description": "REST Path, e.g., /abc/{abc}"}
    )
    method: Optional[str] = field(
        default=None,
        metadata={"description": "REST Method"}
    )
    body: Optional[str] = field(
        default=None,
        metadata={"description": "Request body in json format"}
    )
    headers: Optional[Dict[str, str]] = field(
        default=None,
        metadata={"description": "HTTP Headers"}
    )
    cookies: Optional[Dict[str, str]] = field(
        default=None,
        metadata={"description": "HTTP Cookies"}
    )
    data_override: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "Data override"}
    )
    path_params: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "Path params"}
    )
    query_params: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "Query params"}
    )
    form_params: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "URLEncode Form param value"}
    )
    multipart_params: Optional[list[str]] = field(
        default=None,
        metadata={"description": "multipart param value"}
    )
    expected_code: Optional[str] = field(
        default=None,
        metadata={"description": "Expected Code"}
    )
    func_handler: Optional[Callable] = field(
        default=None,
        metadata={"description": "Dynamic handler"}
    )
    func_handler_type: Optional[Callable] = field(
        default=None,
        metadata={"description": "Dynamic handler type, e.g., python, or javascript"}
    )
    description: Optional[str] = field(
        default=None,
        metadata={"description": "description of request"}
    )
    insecure: Optional[bool] = field(
        default=None,
        metadata={"description": "skip verifying server certificates"}
    )
    asserts: Optional[list[str]] = field(
        default=None,
        metadata={"description": "asserts"}
    )

    def to_json(self) -> str:
        """
        Generates a JSON representation of the request, omitting any fields with None values.

        Returns:
            str: A JSON string containing only non-None fields from the request.
        """
        # Create a dict of only non-None values
        clean_dict = {k: v for k, v in self.__dict__.items() if v is not None}
        return json.dumps(clean_dict, default=str)

    def as_request_dict(self) -> Dict[str, Any]:
        """
        Generates a dictionary representation of the request, omitting any fields with None values.
        The output matches the Go RequestV2 struct format with yaml/json tags.

        Returns:
            Dict[str, Any]: A dictionary containing only non-None fields from the request.
        """
        field_mapping = {
            'name': 'name',
            'url': 'url',
            'path': 'path',
            'method': 'method',
            'body': 'body',
            'headers': 'headers',
            'cookies': 'cookies',
            'data_override': 'data_override',
            'path_params': 'path_params',
            'query_params': 'query_params',
            'form_params': 'form_params',
            'multipart_params': 'multipart_params',
            'expected_code': 'expected_code',
            'func_handler': 'func_handler',
            'func_handler_type': 'func_handler_type',
            'description': 'description',
            'insecure': 'insecure',
            'asserts': 'asserts',
        }

        clean_dict = {}
        for python_field, yaml_field in field_mapping.items():
            value = getattr(self, python_field)
            if value is not None:
                # Check if the field is `body` and if it contains valid JSON
                if python_field == 'body':
                    try:
                        # Format JSON content for multiline YAML representation
                        json_content = json.loads(value)
                        clean_dict[yaml_field] = json.dumps(json_content, indent=2)
                    except json.JSONDecodeError:
                        # If not valid JSON, retain as is
                        clean_dict[yaml_field] = value
                elif python_field == "multipart_params":
                    clean_dict[yaml_field] = [x.to_json() for x in value]
                else:
                    clean_dict[yaml_field] = value
        return clean_dict

    def get_async_value(self, key: str) -> str:
        """
        Get the value of the key from the async data
        """
        return "requests.res." + key

    def set_async_var(self, key: str, value: str) -> None:
        """
        Update the value of the key in the async data
        """
        if self._vars_data is None:
            self._vars_data = {
                "varOverride": {},
                "varExport": {},
            }
        self._vars_data["varOverride"][key] = value

    def export_async_var(self, key: str, value: str) -> None:
        """
        Update the value of the key in the async data
        """
        if self._vars_data is None:
            self._vars_data = {
                "varOverride": {},
                "varExport": {},
            }
        self._vars_data["varExport"][key] = value
