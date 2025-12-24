"""
This module provides the ResponseV2 class for handling HTTP response data in the Skyramp framework.
It includes functionality for converting response data to dictionary format 
and handling JSON body content.
"""
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass, field

@dataclass
class ResponseV2:
    """
    ResponseV2 represents an HTTP response
    """
    description: Optional[str] = field(
        default=None,
        metadata={"description": "description of request"}
    )
    error: Optional[str] = field(
        default=None,
        metadata={"description": "error message when failed"}
    )
    path: Optional[str] = field(
        default=None,
        metadata={"description": "REST path"}
    )
    method: Optional[str] = field(
        default=None,
        metadata={"description": "REST Method"}
    )
    status_code: Optional[int] = field(
            default=None,
            metadata={"description": "HTTP Status Code"}
    )
    cookies : Optional[Dict[str, str]] = field(
            default=None,
            metadata={"description": "HTTP cookie"}
    )
    response_headers: Optional[Dict[str, str]] = field(
            default=None,
            metadata={"description": "HTTP Headers from response"}
    )
    response_body: Optional[str] = field(
            default=None,
            metadata={"description": "Response body in json format"}
    )
    request_headers: Optional[Dict[str, str]] = field(
            default=None,
            metadata={"description": "HTTP Headers from request"}
    )
    request_body: Optional[str] = field(
            default=None,
            metadata={"description": "Request body in json format"}
    )
    duration: Optional[str] = field(
            default=None,
            metadata={"description": "duration of the request"}
    )

    def as_response_dict(self) -> Dict[str, Any]:
        """
        Generates a dictionary representation of the request, omitting any fields with None values.
        The output matches the Go RequestV2 struct format with yaml/json tags.

        Returns:
            Dict[str, Any]: A dictionary containing only non-None fields from the request.
        """
        field_mapping = {
            'description': 'description',
            'error': 'error',
            'path': 'path',
            'method': 'method',
            'status_code': 'status_code',
            'cookies': 'cookies',
            'response_headers': 'response_headers',
            'response_body': 'response_body',
            'request_headers': 'request_headers',
            'request_body': 'request_body',
            'duration': 'duration',
        }

        clean_dict = {}
        for python_field, yaml_field in field_mapping.items():
            value = getattr(self, python_field)
            if value is not None:
                if python_field == 'body':
                    try:
                        # Format JSON content for multiline YAML representation
                        json_content = json.loads(value)
                        clean_dict[yaml_field] = json.dumps(json_content, indent=2)
                    except json.JSONDecodeError:
                        # If not valid JSON, retain as is
                        clean_dict[yaml_field] = value
                else:
                    clean_dict[yaml_field] = value
        return clean_dict
