"""
This module provides the MockV2 class for handling mock configuration data in the Skyramp framework.
It includes functionality for converting mock data to dictionary format 
and handling JSON serialization.
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class MockV2:
    """
    Represents a mock object configuration for API endpoint mocking.
    Provides methods for JSON serialization and dictionary conversion.
    """
    url: str = field(
        metadata={"description": "Base URL for the mock"}
    )
    endpoint: str = field(
        metadata={"description": "API endpoint path"}
    )
    port: int = field(
        metadata={"description": "Port number for the mock service"}
    )
    method: str = field(
        metadata={"description": "HTTP method (GET, POST, etc.)"}
    )
    response_status_code: int = field(
        metadata={"description": "HTTP response status code"}
    )
    body: Optional[str] = field(
        default=None,
        metadata={"description": "Response body content"}
    )
    data_override: Optional[Dict[str, Any]] = field(
        default=None,
        metadata={"description": "Data override for mock configuration"}
    )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the MockV2 object to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the MockV2 object
                with snake_case keys.
        """
        result = {
            "url": self.url,
            "endpoint": self.endpoint,
            "port": self.port,
            "method": self.method,
            "status_code": self.response_status_code,
        }
        if self.body is not None:
            result["response_body"] = self.body
        if self.data_override is not None:
            result["data_override"] = self.data_override

        return result

    def to_json(self) -> str:
        """
        Generates a JSON representation of the mock configuration.

        Returns:
            str: A JSON string containing the mock configuration.
        """
        return json.dumps(self.to_dict())
