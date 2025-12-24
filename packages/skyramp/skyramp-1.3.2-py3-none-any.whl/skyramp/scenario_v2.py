"""
Contains helpers for interacting with Skyramp testing scenarios.
"""

from typing import Optional

from typing_extensions import Self
from skyramp.utils import _get_rest_path_name
from skyramp.test_request2 import RequestV2


class AsyncRequest:
    """' Wrapper class for RequestV2 object"""

    def __init__(self, scenario, request, step_index):
        self.scenario = scenario
        self.request = request
        self.step_index = step_index

    def get_async_request_value(self, path):
        """
        returns request's response value construct for asynchronous backend

        Args:   
            path: The path to the value
        """
        if path is None:
            return f"requests.{self.request.name}.res"
        return f"requests.{self.request.name}.res.{path}"

    def request_status_check(self, code):
        """
        returns request's status check construct for asynchronous backend
        Args:
            code: The expected status code
        """
        return f"requests.{self.request.name}.code == {code}"

    def assert_equal(self, json_path, expected_value):
        """
        adds an assert to the request
        Args:
            code: The expected status code
        """
        # append assert to the request
        self.scenario.steps[self.step_index]["asyncAsserts"].append(
            f"{self.get_async_request_value(json_path)} == {expected_value}"
        )

    def assert_not_equal(self, json_path, value):
        """
        adds an assert to the request
        Args:
            code: The expected status code
        """
        return self.scenario.steps[self.step_index]["asyncAsserts"].append(
            f"{self.get_async_request_value(json_path)} != {value}"
        )


class AsyncScenario:
    """
    Represents a testing scenario.
    """

    def __init__(
        self,
        name: str,
        ignore_failure: Optional[bool] = False,
    ) -> None:
        self.name = name
        self.steps = []
        self.vars = {}
        self.until = ""
        self.max_retries = 5
        self.retry_interval = 1
        self.ignore_failure = ignore_failure

    # pylint: disable=too-many-locals
    def add_async_request(
        self,
        name: Optional[str] = None,
        url: Optional[str] = None,
        path: Optional[str] = None,
        method: Optional[str] = None,
        body: Optional[str] = None,
        headers: Optional[dict] = None,
        path_params: Optional[dict] = None,
        query_params: Optional[dict] = None,
        form_params: Optional[dict] = None,
        multipart_params: Optional[list] = None,
        data_override: Optional[dict] = None,
        description: Optional[str] = None,
        expected_code: Optional[str] = None,
        if_: Optional[str] = "",
        until: Optional[str] = None,
        max_retries: Optional[int] = 5,
        retry_interval: Optional[int] = 1,
        insecure: Optional[bool] = None,
    ):
        """
        Adds an asynchronous request to this scenario.

        Args:
            url: The URL of the request
            path: The path of the request
            method: The HTTP method of the request (e.g., GET, POST)
            body: The body of the request
            headers: The headers of the request
            path_params: The path parameters of the request
            query_params: The query parameters of the request
            form_params: The form parameters of the request
            multipart_params: The multipart parameters of the request
            data_override: The data override for the request
            description: The description of the request
            expected_code: The expected HTTP status code of the request
            if_: The condition to execute the request
            until: The condition to stop retrying
            max_retries: The maximum number of retries
            retry_interval: The interval between retries
        """
        request = RequestV2(
            name=name,
            url=url,
            path=path,
            method=method,
            body=body,
            headers=headers,
            path_params=path_params,
            query_params=query_params,
            form_params=form_params,
            multipart_params=multipart_params,
            data_override=data_override,
            description=description,
            insecure=insecure,
        )
        if not name:
            request.name = _get_rest_path_name(path, method)
        step_request = request.as_request_dict()
        if if_ != "":
            step_request["if"] = if_
        if until != "":
            step_request["repeat"] = {
                "until": until,
                "maxRetries": max_retries,
                "interval": retry_interval,
            }
        step_request["type"] = "request"
        step_request["varOverride"] = {}
        step_request["varExport"] = {}
        step_request["asyncAsserts"] = []
        if expected_code:
            step_request["expected_code"] = expected_code
        self.steps.append(step_request)
        step_index = len(self.steps) - 1
        return AsyncRequest(self, request, step_index)

    def add_async_scenario(
        self,
        nested_scenario: Self,
        until: Optional[str] = "",
        max_retries: Optional[int] = 5,
        retry_interval: Optional[int] = 1,
    ):
        """
        Adds an asynchronous nested scenario to this scenario.

        Args:
            nested_scenario: The nested scenario to add
            until: The condition to stop retrying
        """
        scenario = nested_scenario
        step_scenario = {
            "type": "scenario",
            "scenario": scenario,
        }
        self.until = until
        if self.until != "":
            self.max_retries = max_retries
            self.retry_interval = retry_interval
        self.steps.append(step_scenario)

    def set_async_var(self, var_name, value):
        """
        sets a scenario level variable
        Args:
            var_name: The name of the variable
            value: The value of the variable
        """
        if self.vars is None:
            self.vars = {}
        self.vars[var_name] = value

    def get_async_var(self, var_name):
        """
        returns scenario's variable construct for asynchronous backend
        Args:
            var_name: The name of the variable
        """
        return f"vars.{var_name}"

    def get_async_scenario_value(self, var):
        """
        returns scenario's response value construct for asynchronous backend
        Args:
            var: The name of the variable
        """
        return f"scenarios.{self.name}.{var}"

    def export_async_var(self, var_name, value):
        """
        sets a scenario level variable for export
        Args:
            var_name: The name of the variable
            value: The value of the variable

        """
        self.steps.append({"type": "varExport", "name": var_name, "value": value})

    def add_assert(self, value):
        """
        adds an assert to the scenario
        Args:
            value: The value to assert  
        """
        self.steps.append({"type": "assert", "assert": value})

    def to_json(self):
        """
        Converts this scenario to JSON.
        """
        # iterate through the steps and convert them to JSON
        steps = []
        for step in self.steps:
            if step["type"] == "request":
                steps.append({"request": step})
            elif step["type"] == "scenario":
                if isinstance(step["scenario"], AsyncScenario):
                    steps.append({"scenario": step["scenario"].to_json()})
            elif step["type"] == "varExport":
                steps.append({"varExport": {step["name"]: step["value"]}})
        return {
            "name": self.name,
            "steps": steps,
            "vars": self.vars,
            "until": self.until,
            "maxRetries": self.max_retries,
            "interval": self.retry_interval,
            "ignoreFailure": self.ignore_failure,
        }
