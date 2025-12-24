"""
Contains helpers for interacting with Skyramp mock object.
"""

from typing import List
from skyramp.response import _ResponseValue as ResponseValue
from skyramp.traffic_config import _TrafficConfig

class _Mock:
    def __init__(
            self,
            version: str,
            responses: List[ResponseValue],
            traffic_config: _TrafficConfig,
            proxies: List[ResponseValue]) -> None:
        self.version = version
        self.responses = responses
        self.traffic_config = traffic_config
        self.proxies = proxies

    def to_json(self):
        """
        Convert the Mock object to a JSON string.
        """
        mock = {
            "version": self.version,
            "responses": self.responses,
        }

        if self.traffic_config is not None:
            mock.update(self.traffic_config.to_json())
        if self.proxies is not None:
            mock["proxies"] = self.proxies

        return mock
