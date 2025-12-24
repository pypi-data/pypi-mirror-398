"""
Contains helpers for interacting with Skyramp test description.
"""

from typing import List
from skyramp.test import _Test as Test
from skyramp.test_request import _Request as Request
from skyramp.scenario import _Scenario as Scenario
from skyramp.service import _Service as Service
from skyramp.endpoint import _Endpoint as Endpoint

class _TestDescription:
    def __init__(
            self, version: str,
            test: Test,
            test_group_id: str,
            scenarios: List[Scenario],
            requests: List[Request],
            endpoints: List[Endpoint],
            services: List[Service]) -> None:
        self.version = version
        self.test = test
        self.test_group_id = test_group_id
        self.scenarios = scenarios
        self.requests = requests
        self.endpoints = endpoints
        self.services = services

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        return {
            "version": self.version,
            "testGroupId": self.test_group_id,
            "test": self.test,
            "scenarios": self.scenarios,
            "requests": self.requests,
            "services": self.services,
            "endpoints": self.endpoints,
        }
