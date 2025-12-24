"""
Contains helpers for interacting with Skyramp mock object.
"""

from typing import Optional, Dict
from skyramp.response import _ResponseValue as ResponseValue

class _MockObject:
    def __init__(
            self,
            name: str,
            response_value: ResponseValue,
            blob_override: Optional[Dict] = None
        ) -> None:
        self.name = name
        self.response_value = response_value
        self.blob_override = blob_override if blob_override is not None else {}
