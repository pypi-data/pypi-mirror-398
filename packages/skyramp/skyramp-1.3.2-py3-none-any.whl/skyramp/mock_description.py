"""
Contains helpers for interacting with Skyramp mock description.
"""

from typing import List
from skyramp.service import _Service as Service
from skyramp.endpoint import _Endpoint as Endpoint
from skyramp.response import _ResponseValue as ResponseValue
from skyramp.mock import _Mock as Mock

class _MockDescription:
    def __init__(
            self,
            version: str,
            mock: Mock,
            responses: List[ResponseValue],
            endpoints: List[Endpoint],
            services: List[Service]) -> None:
        self.version = version
        self.mock = mock
        self.responses = responses
        self.endpoints = endpoints
        self.services = services

    def to_json(self):
        """
        Convert the mock description object to a JSON string.
        """
        return {
            "version": self.version,
            "mock": self.mock,
            "responses": self.responses,
            "services": self.services,
            "endpoints": self.endpoints,
        }
