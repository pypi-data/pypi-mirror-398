""" TestStatusV3 class for interactive mode """

from typing import List, Dict
from skyramp.test_status import RawTestResult, TestResultType

class ScenarioStatus:
    """
    ScenarioStatus object
    """

    overall_status: RawTestResult = {}
    request_list: List[RawTestResult] = []
    child_scenarios: List[RawTestResult] = {}

    def get_request_status(self, request_name):
        """
        Returns the request status for the given request name
        """
        for req in self.request_list:
            if req.name == request_name:
                return req
        return None

    def get_child_scenario_status(self, scenario_name):
        """
        Returns the child scenario status for the given scenario name
        """
        for val in self.child_scenarios:
            if val.name == scenario_name:
                return val
        return None

    def __repr__(self):
        return (
            "ScenarioStatus("
            f"overall_status='{self.overall_status}',"
            f"request_status='{self.request_list}',"
            f"child_scenarios= '{self.child_scenarios}' )"
        )

class TestStatusV3:
    """
    TestStatusV3 object
    """

    scenario_dict: Dict[str, RawTestResult] = {}
    request_dict: Dict[str, Dict[str, RawTestResult]] = {}
    child_scenarios_dict: Dict[str, Dict[str, RawTestResult]] = {}

    # pylint: disable=too-many-locals
    def __init__(self, options: dict):
        results = options.test_results
        for res in results:
            for result in res:
                result_type = result.type
                nested_info = result.nested_info
                parent = result.parent
                # if the result is a scenario, add it to the scenario_dict
                if result_type == TestResultType.Scenario:
                    # get the scenario name
                    path_list = result.description.split(".")
                    scenario_name = path_list[-1]
                    result.name = scenario_name
                    result.description = None
                    if parent == "":
                        self.scenario_dict[nested_info] = result
                    else:
                        self.scenario_dict[nested_info] = result
                        if parent not in self.scenario_dict:
                            self.scenario_dict[parent] = {}
                        if self.child_scenarios_dict.get(parent) is None:
                            self.child_scenarios_dict[parent] = {}
                        self.child_scenarios_dict[parent][nested_info] = result
                elif result_type == TestResultType.Request:
                    if self.request_dict.get(parent) is None:
                        self.request_dict[parent] = {}
                    self.request_dict[parent][nested_info] = result

    def get_scenario_status(self, scenario_name) -> ScenarioStatus:
        """
        Returns the scenario status for the given scenario name
        """
        for val in self.scenario_dict.values():
            if val.name == scenario_name:
                scenario_status = ScenarioStatus()
                scenario_status.overall_status = val

                # get the request status for the scenario
                req_list = self.request_dict.get(val.nested_info, {})
                request_list = []
                for value in req_list.values():
                    request_list.append(
                        RawTestResult(
                            options={
                                "name": value.name,
                                "input": value.input,
                                "output": value.output,
                            }
                        )
                    )
                scenario_status.request_list = request_list

                # get the child scenario status for the scenario
                child_scenarios = self.child_scenarios_dict.get(val.nested_info, {})
                child_scenario_list = []
                for value in child_scenarios.values():
                    child_scenario_list.append(
                        RawTestResult(
                            options={
                                "name": value.name,
                                "status": value.status,
                                "error": value.error,
                            }
                        )
                    )
                    if value.error != "":
                        if scenario_status.overall_status.error == "":
                            scenario_status.overall_status.error = (
                                "'" + value.error + "'"
                            )
                        else:
                            scenario_status.overall_status.error += (
                                ", '" + value.error + "'"
                            )

                scenario_status.child_scenarios = child_scenario_list
                return scenario_status
        return None

    def __repr__(self):
        return "TestStatusV3(" f"scenarios='{self.scenario_dict.values()}' )"
