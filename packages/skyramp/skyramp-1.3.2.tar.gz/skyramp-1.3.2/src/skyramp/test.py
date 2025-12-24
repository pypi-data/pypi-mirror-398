"""
Contains helpers for interacting with Skyramp test object.
"""

from skyramp.test_pattern import _TestPattern as TestPattern


class _Test:
    def __init__(self, name: str, test_pattern: TestPattern) -> None:
        self.name = name
        self.test_pattern = test_pattern

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        json_data = {}
        if hasattr(self, "name") and self.name is not None:
            json_data["name"] = self.name
        if hasattr(self, "test_pattern") and self.test_pattern is not None:
            json_data["testPattern"] = (TestPattern.to_json(self.test_pattern),)
        return json_data


def get_global_var(var_name):
    """
    construct backend interpretation of accessing globalVars
    """
    return f"globalVars.{var_name}"
