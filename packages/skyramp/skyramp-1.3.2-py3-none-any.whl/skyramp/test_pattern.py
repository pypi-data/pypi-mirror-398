"""
Contains helpers for interacting with Skyramp test pattern.
"""
class _TestPattern:
    def __init__(self, scenario_name: str, request_name: str, start_at: str) -> None:
        self.scenario_name = scenario_name
        self.request_name = request_name
        self.start_at = start_at

        self.test_pattern = {
            "scenario_name": self.scenario_name,
            "request_name": self.request_name,
            "start_at": self.start_at,
        }

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        return {
            "scenarioName": self.scenario_name,
            "requestName": self.request_name,
            "startAt": self.start_at,
        }
