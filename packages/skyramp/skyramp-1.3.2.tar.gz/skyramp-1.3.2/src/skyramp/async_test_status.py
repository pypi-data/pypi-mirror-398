"""
TestStatus module
"""

import json
import ctypes
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from functools import cmp_to_key
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn, RobotNotRunningError
from skyramp.utils import _library
from skyramp.test_status import _get_response_value, ResponseLog, TesterState
from skyramp.test_status import (
    TestResultType,
    TestStat,
    RawTestResult,
    TestTimeseriesStat,
)
from skyramp.utils import sanitize_payload, sanitize_headers_and_cookies


class AsyncTestStatus(ABC):
    """
    AsyncTestStatus object
    """

    test_status: dict = {}
    test_id: str = ""
    test_type: str = ""

    def __init__(self, options: dict):
        self.test_id = options.get("id", "")
        self.test_status = options

    def get_test_id(self) -> str:
        """
        Returns the test id
        """
        return self.test_id

    def get_test_type(self) -> str:
        """
        Returns the test type
        """
        return self.test_type

    @abstractmethod
    def get_scenario(self, scenario_name: str) -> "BaseAsyncScenarioStatus":
        """
        Get the scenario
        """

    @abstractmethod
    def get_scenarios(self, scenario_name: str = "") -> List["BaseAsyncScenarioStatus"]:
        """
        Get the scenarios
        """

    @abstractmethod
    def get_request(
        self, scenario_name: str, request_name: str
    ) -> "BaseAsyncRequestStatus":
        """
        Get the request
        """

    def get_overall_status(self) -> str:
        """
        Get the overall status using the library function
        """
        func = _library.getOverallStatusWrapper
        func.argtypes = [ctypes.c_char_p]
        func.restype = ctypes.c_char_p
        result = func(json.dumps(self.test_status).encode("utf-8"))
        return result.decode("utf-8")

    @staticmethod
    def create(options: dict) -> "AsyncTestStatus":
        """
        Create the appropriate TestStatus object based on the options
        """
        if (
            "results" in options
            and len(options["results"]) > 1
            and "type" in options["results"][1]
            and options["results"][1]["type"] == "load"
        ):
            return AsyncLoadTestStatus(options)
        return AsyncIntegrationTestStatus(options)


class BaseAsyncRequestStatus(ABC):
    """
    BaseAsyncRequestStatus object
    """

    def __init__(self, result_object: dict):
        self.name = ""
        self.id = ""
        self.result_object = ""
        self.json_object = result_object
        self.asserts = []

    def __repr__(self) -> str:
        return (
            f"BaseAsyncRequestStatus(name={self.name}, "
            f"status={self.result_object}, asserts={self.asserts})"
        )

    @abstractmethod
    def get_load_test_response(
        self, status_code: str, json_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the response of the load test
        """

    @abstractmethod
    def get_response(self, json_path: Optional[str] = None) -> Optional[str]:
        """
        Get the response of the request
        """

    @abstractmethod
    def get_var_value(self, key: str) -> str:
        """
        Get the value of the variable
        """


class BaseAsyncScenarioStatus(ABC):
    """
    BaseAsyncScenarioStatus object
    """

    def __init__(self, data_object: dict):
        self.result: str = data_object
        self.name = ""
        self.overall_status = {}
        self.timeseries = []
        self.sub_scenarios: List["BaseAsyncScenarioStatus"] = []
        self.requests: List["BaseAsyncRequestStatus"] = []

    @abstractmethod
    def get_sub_scenarios(self) -> List["BaseAsyncScenarioStatus"]:
        """
        Get the sub scenarios
        """

    @abstractmethod
    def get_request(self, request_name: str) -> "BaseAsyncRequestStatus":
        """
        Get the request based on the request name
        """

    @abstractmethod
    def get_requests(self) -> List["BaseAsyncRequestStatus"]:
        """
        Get the requests
        """

    @abstractmethod
    def get_overall_status(self) -> str:
        """
        Get the overall status
        """

    @abstractmethod
    def get_var_value(self, key: str) -> str:
        """
        Get the value of the variable
        """


class AsyncLoadTestStatus(AsyncTestStatus):
    """
    AsyncTestTypeStatus object
    """

    class AsyncScenarioStatus(BaseAsyncScenarioStatus):
        """
        AsyncScenarioStatus object
        """

        timeseries: Optional[List[TestTimeseriesStat]] = None

        def __init__(self, data_object: dict):
            super().__init__({})
            data_object = TestStat(data_object)
            self.result: str = data_object
            self.name = data_object.description.split(".")[-1]
            self.id = data_object.id
            self.stats: TestStat = data_object
            self.sub_scenarios: List["AsyncLoadTestStatus.AsyncScenarioStatus"] = []
            self.requests: List["AsyncLoadTestStatus.AsyncRequestStatus"] = []

        def __repr__(self) -> str:
            return (
                f"AsyncScenarioStatus(name={self.name}, "
                f"status={self.stats.__repr__()}, "
                f"sub_scenarios={self.sub_scenarios}, requests={self.requests})"
            )

        def __str__(self) -> str:
            # iterate over the requests and get the request status
            request_status = []
            for request in self.requests:
                # iterate over the request table and get the request status
                log_tables = request.result_object.log_table
                for status_code, json_data in log_tables.items():
                    log_tables[status_code] = json.loads(json_data)
                request_status.append(request.to_json())
            return json.dumps(
                {
                    "name": self.name,
                    "status": self.stats.to_json(),
                    # "sub_scenarios": self.sub_scenarios,
                    "requests": request_status,
                },
                indent=2,
                ensure_ascii=False,
            )

        def get_sub_scenarios(self) -> List["AsyncLoadTestStatus.AsyncScenarioStatus"]:
            # sort the sub scenarios based on the id
            self.sub_scenarios.sort(key=cmp_to_key(_sort_keys))
            return self.sub_scenarios

        def get_request(
            self, request_name: str
        ) -> "AsyncLoadTestStatus.AsyncRequestStatus":
            request_list = []
            for request in self.requests:
                if request.result_object.description.endswith("." + request_name):
                    request_list.append(request)
            if len(request_list) == 1:
                return request_list[0]
            # throw error that request not found
            if len(request_list) == 0:
                raise KeyError(f"Request {request_name} not found in the scenario")
            # throw error that multiple requests found
            if len(request_list) > 1:
                raise KeyError(
                    f"Multiple requests found with the name {request_name}, "
                    "please iterate over the requests"
                )
            return None

        def get_requests(self) -> List["AsyncLoadTestStatus.AsyncRequestStatus"]:
            self.requests.sort(key=cmp_to_key(_sort_keys))
            return self.requests

        def get_overall_status(self) -> str:
            status = {"name": self.name, "stats": self.stats.get_stats()}
            if self.timeseries is not None:
                status["timeseries"] = [ts.__dict__ for ts in self.timeseries]

            return json.dumps(status, indent=2, ensure_ascii=False)

        def get_var_value(self, key: str) -> str:
            raise NotImplementedError

    class AsyncRequestStatus(BaseAsyncRequestStatus):
        """
        AsyncRequestStatus object
        """

        def __init__(self, result_object: dict):
            super().__init__(result_object)
            result_object = TestStat(result_object)
            self.test_status = result_object
            self.name = result_object.description.split(".")[-1]
            self.id = result_object.id
            self.result_object = result_object
            self.asserts = []

        def __repr__(self) -> str:
            return (
                f"AsyncRequestStatus(name={self.name}, "
                f"status={self.result_object}, asserts={self.asserts})"
            )

        def to_json(self) -> Dict[str, Any]:
            """
            Convert the object to json
            """
            return {
                "name": self.name,
                "status": self.result_object.to_json(),
                "asserts": [assert_stat.to_json() for assert_stat in self.asserts],
            }

        def get_load_test_response(
            self, status_code: str, json_path: Optional[str] = None
        ) -> Optional[str]:
            json_data = self.result_object.log_table.get(status_code, None)
            if json_data is None:
                return None
            json_response = json_data.get("Response", None)
            if json_response is not None:
                payload = json_response.get("payload", None)
                if json_response is None:
                    return None
                if json_path is None:
                    return json.dumps(payload, indent=2)
                return _get_response_value(payload, json_path)
            return None

        def get_response(self, json_path: Optional[str] = None) -> Optional[str]:
            raise NotImplementedError

        def get_var_value(self, key: str) -> str:
            raise NotImplementedError

    scenario_dict: Dict[str, AsyncScenarioStatus] = {}

    # pylint: disable=too-many-locals,too-many-branches,too-many-nested-blocks
    def __init__(self, options: dict):
        super().__init__(options)
        self.test_status = options
        self.test_id = options.get("id", "")
        self.test_type = "load"
        if options and options.get("results") is None:
            return
        results = options["results"]
        for result in results[1:]:
            raw_result = RawTestResult(result)
            if raw_result.error != "":
                raise ValueError(raw_result.error)
            stats = raw_result.stat
            for key, result in stats.items():
                result_stat = TestStat(result)
                result["id"] = key
                result_id = result_stat.description
                if result_stat.type == TestResultType.Scenario:
                    new_scenario = AsyncLoadTestStatus.AsyncScenarioStatus(result)
                    self.scenario_dict[result_id] = new_scenario
                elif result_stat.type == TestResultType.Request:
                    # keep dropping the .<> from the result_id to get the parent scenario
                    item_list = result_id.split(".")
                    for i in reversed(range(len(item_list))):
                        item_list.pop(i)
                        parent_scenario = ".".join(item_list[:-1])
                        if parent_scenario in self.scenario_dict:
                            request = AsyncLoadTestStatus.AsyncRequestStatus(result)
                            self.scenario_dict[parent_scenario].requests.append(request)
                            break
                elif result_stat.assert_statement is not None:
                    item_list = result_stat.description.split(".")
                    scenario_id = ""
                    request_id = ""
                    # get scenario id from the description
                    if len(item_list) > 4:
                        scenario_id = ".".join(item_list[:-4])
                        request_id = ".".join(item_list[:-2])
                    # read the scenario and request from the scenario_dict
                    if scenario_id in self.scenario_dict:
                        scenario = self.scenario_dict[scenario_id]
                        for request in scenario.get_requests():
                            if request.result_object.description == request_id:
                                request.asserts.append(result_stat)
                                break

            if raw_result.type == TestResultType.Load:
                timeseries_list = []
                if raw_result.timeseries is not None:
                    for timeseries in raw_result.timeseries:
                        timeseries_list.append(TestTimeseriesStat(timeseries))
                if raw_result.description in self.scenario_dict:
                    self.scenario_dict[raw_result.description].timeseries = (
                        timeseries_list
                    )

    def get_scenario(self, scenario_name: str) -> AsyncScenarioStatus:
        scenario_list = self.get_scenarios(scenario_name)
        if len(scenario_list) == 1:
            return scenario_list[0]
        # throw error that scenario not found
        if len(scenario_list) == 0:
            raise KeyError(f"Scenario {scenario_name} not found in the test")
        # throw error that multiple scenarios found
        if len(scenario_list) > 1:
            raise KeyError(
                f"Multiple scenarios found with the name {scenario_name}, "
                "please iterate over the scenarios"
            )
        return None

    def get_scenarios(self, scenario_name: str = "") -> List[AsyncScenarioStatus]:
        # sort the scenarios based on the id
        scenario_list = sorted(self.scenario_dict.values(), key=cmp_to_key(_sort_keys))
        if scenario_name == "":
            return list(scenario_list)
        scenarios = []
        # iterate over the scenario_dict and get scenario for the given scenario_name
        for scenario in scenario_list:
            if scenario.name == scenario_name:
                scenarios.append(scenario)
        return scenarios

    def get_request(self, scenario_name: str, request_name: str) -> AsyncRequestStatus:
        scenario = self.get_scenario(scenario_name)
        return scenario.get_request(request_name)


class AsyncIntegrationTestStatus(AsyncTestStatus):
    """
    AsyncIntegrationTestStatus object
    """

    class AsyncScenarioStatus(BaseAsyncScenarioStatus):
        """
        AsyncScenarioStatus object
        """

        def __init__(self, data: dict):
            super().__init__(data)
            data = RawTestResult(data)
            desc_list = data.description.split(".")
            self.name: str = desc_list[-1]
            self.id = data.id
            self.status = data.status
            self.error = data.error
            self.step_description = data.step_description
            self.step_name = data.step_name
            self.sub_scenarios: List[
                "AsyncIntegrationTestStatus.AsyncScenarioStatus"
            ] = []
            self.requests: List["AsyncIntegrationTestStatus.AsyncRequestStatus"] = []

        def __repr__(self) -> str:
            return (
                f"AsyncScenarioStatus(name={self.name}, "
                f"status={self.status.__repr__()}, error={self.error})"
            )

        def get_sub_scenarios(
            self,
        ) -> List["AsyncIntegrationTestStatus.AsyncScenarioStatus"]:
            """
            Get sub scenarios from the scenario
            """
            return self.sub_scenarios

        def get_request(
            self, request_name: str
        ) -> "AsyncIntegrationTestStatus.AsyncRequestStatus":
            """
            Get request from the scenario
            """
            request_list = []
            for request in self.requests:
                if request.result_object.description.endswith("." + request_name):
                    request_list.append(request)
            if len(request_list) == 1:
                return request_list[0]
            # throw error that request not found
            if len(request_list) == 0:
                raise KeyError(f"Request {request_name} not found in the scenario")
            # throw error that multiple requests found
            if len(request_list) > 1:
                raise KeyError(
                    f"Multiple requests found with the name {request_name}, "
                    "please iterate over the requests"
                )
            return None

        def get_requests(self) -> List["AsyncIntegrationTestStatus.AsyncRequestStatus"]:
            """
            Get requests from the scenario
            """
            # sort the requests based on the id
            self.requests.sort(key=cmp_to_key(_sort_keys))
            return self.requests

        def get_overall_status(self) -> str:
            """
            Get overall status of the scenario
            """
            return json.dumps(
                {
                    "name": self.name,
                    "status": self.status,
                    "error": self.error,
                },
                indent=2,
                ensure_ascii=False,
            )

        def assert_status(self) -> bool:
            """
            Assert the status of the scenario
            """
            return self.status

        def get_var_value(self, key: str) -> str:
            # from the last request in the scenario get the var value
            if len(self.requests) > 0:
                request = self.requests[-1]
                if request.result_object is not None:
                    return request.get_var_value(key)
            # if no request found then check the scenario
            return f"Key '{key}' not found in the scenario"

    class AsyncRequestStatus(BaseAsyncRequestStatus):
        """
        AsyncRequestStatus object
        """

        def __init__(self, result_object: dict) -> None:
            super().__init__(result_object)
            result_object = RawTestResult(result_object)
            self.result_object = result_object
            self.id = result_object.id
            self.name = result_object.description.split(".")[-1]
            self.asserts = []

        def __repr__(self) -> str:
            return (
                f"AsyncRequestStatus(name={self.result_object.name}, "
                f"status={self.result_object.status})"
            )

        def get_response(self, json_path: Optional[str] = None) -> Optional[str]:
            output = ResponseLog(self.result_object.output)
            if output is None:
                return None
            return _get_response_value(output.payload, json_path)

        def get_var_value(self, key: str) -> str:
            state_object = TesterState(self.result_object.state)
            if state_object is not None:
                # check var in export ->vars ->scenario vars and return
                if (
                    key in state_object.exports
                    and state_object.exports[key] is not None
                ):
                    return state_object.exports[key]
                if key in state_object.vars and state_object.vars[key] is not None:
                    return state_object.vars[key]
                if (
                    key in state_object.scenario_vars
                    and state_object.scenario_vars[key] is not None
                ):
                    return state_object.scenario_vars[key]
            raise KeyError(f"Key {key} not found in the async data")

        def get_load_test_response(
            self, status_code: str, json_path: Optional[str] = None
        ) -> Optional[str]:
            raise NotImplementedError

    scenario_dict: Dict[str, AsyncScenarioStatus] = {}

    def __init__(self, options: dict):
        super().__init__(options)
        self.test_id = options.get("id", "")
        self.test_type = "integration"
        if options and options.get("results") is None:
            return
        for result in options["results"][1:]:
            result_object = RawTestResult(result)
            if result_object.type == TestResultType.Scenario:
                self.scenario_dict[result_object.nested_info] = (
                    AsyncIntegrationTestStatus.AsyncScenarioStatus(result)
                )
                if result_object.parent is not None and result_object.parent != "":
                    if result_object.parent in self.scenario_dict:
                        self.scenario_dict[result_object.parent].sub_scenarios.append(
                            self.scenario_dict[result_object.nested_info]
                        )
            elif result_object.type == TestResultType.Request:
                if result_object.parent not in self.scenario_dict:
                    self.scenario_dict[result_object.parent] = (
                        AsyncIntegrationTestStatus.AsyncScenarioStatus(result)
                    )
                self.scenario_dict[result_object.parent].requests.append(
                    AsyncIntegrationTestStatus.AsyncRequestStatus(result)
                )

    def get_scenario(self, scenario_name: str) -> AsyncScenarioStatus:
        """
        Returns the scenario for the given scenario name
        """
        scenario_list = self.get_scenarios(scenario_name)
        if len(scenario_list) == 1:
            return scenario_list[0]
        # throw error that scenario not found
        if len(scenario_list) == 0:
            raise KeyError(f"Scenario {scenario_name} not found in the test")
        # throw error that multiple scenarios found
        if len(scenario_list) > 1:
            raise KeyError(
                f"Multiple scenarios found with the name {scenario_name}, "
                "please iterate over the scenarios"
            )
        return None

    def get_scenarios(self, scenario_name: str = "") -> List[AsyncScenarioStatus]:
        """
        Returns the scenarios
        """
        # sort the scenarios based on the id
        scenario_list = sorted(self.scenario_dict.values(), key=cmp_to_key(_sort_keys))
        if scenario_name == "":
            return list(scenario_list)
        scenarios = []
        # iterate over the scenario_dict and get scenario for the given scenario_name
        for scenario in scenario_list:
            # check scenario description ends with the scenario_name
            if scenario.name == scenario_name:
                scenarios.append(scenario)
        return scenarios

    def get_request(self, scenario_name: str, request_name: str) -> AsyncRequestStatus:
        """
        Returns the request for the given scenario name and request name
        """
        scenario = self.get_scenario(scenario_name)
        return scenario.get_request(request_name)



@keyword
def log_load_metrics_to_robot(test_status: AsyncTestStatus) -> None:
    """Log to robot"""
    divider_text = "============================================================"
    request_divider_text = (
        "------------------------------------------------------------"
    )
    try:
        # log scenario request and response
        for scenario in test_status.get_scenarios(""):
            _log_data(divider_text)
            _log_data(
                f"<b>Scenario Name:</b> <span>{ scenario.name }</span>",
                html=True,
            )
            _log_data(
                f"<b>Stats:</b> { scenario.stats.to_json() }",
                html=True,
            )
            _log_data(divider_text)
            for request in scenario.get_requests():
                _log_data(
                    f"<b>Request Name:</b> <span>{ request.name }</span>", html=True
                )
                _log_data(
                    f"<b>Stats:</b> { request.result_object.get_stats() }",
                    html=True,
                )
                _log_data(request_divider_text)
                _log_data(divider_text)
                # add divider to club status code and response for each request

                for status_code, json_data in request.result_object.log_table.items():
                    json_data = json.loads(json_data)
                    _log_data(
                        f"<b>Status Code:</b> <span>{ status_code }</span>",
                        html=True,
                    )
                    request = json_data.get("Request", None)
                    if request is not None:
                        _log_data(
                            f"<b>Request:</b> <span>{ _sanitize_data(request) }</span>",
                            html=True,
                        )
                    response = json_data.get("Response", None)
                    if response is not None:
                        _log_data(
                            f"<b>Response:</b> <span>{ _sanitize_data(response) }</span>",
                            html=True,
                        )

                    _log_data(divider_text)
                _log_data(request_divider_text)
            _log_data(divider_text)
    except RobotNotRunningError as err:
        print(f"failed to log data to robot: {str(err)}")


def _sanitize_data(data: dict) -> dict:
    """
    Sanitize the data
    """
    # remove service object
    if "service" in data:
        data.pop("service")
    if "payload" in data:
        data["payload"] = sanitize_payload(data["payload"])
    if "headers" in data:
        data["headers"] = sanitize_headers_and_cookies(data["headers"])
    if "cookies" in data:
        data["cookies"] = sanitize_headers_and_cookies(data["cookies"])
    return data


def _log_data(text: str, html: bool = False) -> None:
    """Add divider"""
    BuiltIn().log(
        text,
        html=html,
        level="INFO",
    )


def _sort_keys(entry1: Any, entry2: Any) -> int:
    """
    Sort keys based on the provided logic.
    """
    entry1_list = entry1.id.split(".")
    entry2_list = entry2.id.split(".")

    for part1, part2 in zip(entry1_list, entry2_list):
        try:
            part1_num = int(part1[1:]) if part1[1:].isdigit() else part1
            part2_num = int(part2[1:]) if part2[1:].isdigit() else part2
        except ValueError:
            part1_num, part2_num = part1, part2

        if part1_num != part2_num:
            return -1 if part1_num < part2_num else 1

    # Compare lengths if all parts are equal
    return len(entry1_list) - len(entry2_list)


def get_current_request_response(json_path: str) -> str:
    """
    Get the current request response
    """
    return f"res.{json_path}"
