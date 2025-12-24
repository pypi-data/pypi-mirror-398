"""
Contains helpers for interacting with Skyramp testing scenarios.
"""

import ctypes
from typing import Callable, Optional, List
import inspect
import json
import os
import textwrap
import yaml

from typing_extensions import Self
from skyramp.utils import _library, _call_function
from skyramp.endpoint import _Endpoint
from skyramp.test_request import _Request
from skyramp.test_assert import _Assert


class _Step:
    # pylint: disable=too-many-locals
    def __init__(
        self,
        step,
        max_retries: Optional[int] = 0,
        interval: Optional[str] = "",
        until: Optional[str] = "",
        blob_override: Optional[dict] = None,
        blob_removal: Optional[List[str]] = None,
        vars_override: Optional[dict] = None,
        path_override: Optional[dict] = None,
        query_override: Optional[dict] = None,
        form_override: Optional[dict] = None,
        description: Optional[str] = None,
        step_name: Optional[str] = None,
        break_: Optional[bool] = False,
        ignore: Optional[bool] = False,
        if_: Optional[str] = None,
        export: Optional[dict] = None,
        until_func: Optional[Callable] = None,
        wait: Optional[str] = "",
        with_: Optional[str] = "",
        expected_code: Optional[int] = 0,
        unexpected_code: Optional[int] = 0,
    ) -> None:
        self.step = step
        self.max_retries = max_retries
        self.interval = interval
        self.until = until
        self.response_value = None
        self.cookie_value = None
        self.response_code = 0
        self.vars_override = vars_override
        self.path_override = path_override
        self.query_override = query_override
        self.form_override = form_override
        self.blob_override = blob_override
        self.blob_removal = blob_removal
        self.description = description
        self.step_name = step_name
        self.break_ = break_
        self.ignore = ignore
        self.if_ = if_
        self.export = export
        self.until_func = until_func
        self.wait = wait
        self.with_ = with_
        self.expected_code = expected_code
        self.unexpected_code = unexpected_code

    def override_vars(self, vars_: Optional[dict]):
        """
        Overrides the vars for this step
        """
        self.vars_override = vars_

    def override_blob(self, blob_override: Optional[dict]):
        """
        Overrides the blob for this step
        """
        self.blob_override = blob_override

    def set_value(self, response_value: json):
        """
        Sets the response value for this step
        """
        self.response_value = response_value

    def set_cookie_value(self, cookie_value: json):
        """
        Sets the cookie value for this step
        """
        self.cookie_value = cookie_value

    def get_request(self):
        """
        Gets the request value for this step
        """
        if self.step is not None and isinstance(self.step, _Request):
            if not self.step.name.startswith("requests."):
                return f"requests.{self.step.name}"
            return f"{self.step.name}"
        raise Exception("Step is not a request")

    def get_scenario(self):
        """
        Gets the scenario for this step
        """
        if self.step is not None and isinstance(self.step, _Scenario):
            if not self.step.name.startswith("scenarios."):
                return f"scenarios.{self.step.name}"
            return f"{self.step.name}"
        raise Exception("Step is not a scenario")

    def get_scenario_value(self, json_path: str):
        """
        Gets the response value for this step
        """
        scenario = self.get_scenario()
        return f"{scenario}.{json_path}"

    def get_response_code(self):
        """
        Gets the response code for this step
        """
        request = self.get_request()
        return f"{request}.code"

    def get_response_value(self, json_path: str = "") -> str:
        """
        Gets the response value for this step based on the provided JSON path.
        If the JSON path is empty, it returns the entire response.

        Example JSON path: "body.data"
        """
        request = self.get_request()
        if json_path == "":
            return f"{request}.res"
        return f"{request}.res.{json_path}"

    def get_response_cookies_value(self, json_path: str):
        """
        Gets the response value for this step
        """
        request = self.get_request()
        return f"{request}.cookies.{json_path}"

    # pylint: disable=too-many-branches
    def to_json(self):
        """
        Convert the object to dictionary
        """
        step_dict = self.step.to_json()

        # Include other attributes with values that are not None
        additional_attributes = {
            "description": self.description,
            "name": self.step_name,
            "override": self.vars_override,
            "pathOverride": self.path_override,
            "queryOverride": self.query_override,
            "formOverride": self.form_override,
            "blobOverride": self.blob_override,
            "blobRemoval": self.blob_removal,
            "break": self.break_,
            "ignore": self.ignore,
            "if": self.if_,
            "export": self.export,
            "wait": self.wait,
            "with": self.with_,
        }
        step_dict.update({k: v for k, v in additional_attributes.items() if v is not None})

        # Prepare 'repeat' dictionary if relevant attributes are set
        repeat_settings = {k: getattr(self, k)
            for k in ["maxRetries", "interval", "until", "with_"]
            if getattr(self, k)}
        if repeat_settings:
            step_dict["repeat"] = repeat_settings

        # Include Python function source if 'until_func' is provided
        if self.until_func:
            step_dict["repeat"]["untilPython"] = textwrap.dedent(inspect.getsource(self.until_func))
            step_dict["repeat"]["untilPythonFuncName"] = self.until_func.__name__

        if self.expected_code != 0:
            step_dict["expectedCode"] = self.expected_code
        if self.unexpected_code != 0:
            step_dict["unexpectedCode"] = self.unexpected_code

        return step_dict


class _Scenario:
    """
    Represents a testing scenario.
    """

    def __init__(
        self,
        name: str,
        start_at: int = 1,
        vars_: Optional[dict] = None,
        headers: Optional[dict] = None,
        ignore: bool = False,
    ) -> None:
        self.name = name
        self.steps = []
        self.steps_v1 = []
        self.steps_v2 = []

        self.global_headers = {}

        self.services = []
        self.endpoints = []
        self.requests = []
        self.scenarios = []
        self.start_at = start_at
        self.vars = vars_
        self.headers = headers

        self.ignore = ignore

    def add_request(
        self,
        endpoint: _Endpoint,
        method_name: str,
        request_object=None,
        dynamic: bool = False,
    ) -> str:
        """
        Adds a request to this scenario.

        Args:
            endpoint: The endpoint object associated with the request
            method_name: The name of the method that this request will be hitting
            request_object: Map containing request information
            dynamic: Whether or not the request_object is a dynamic script

        Returns:
            The name of the request that was added
        """
        self._build_metadata_for_endpoint(endpoint)

        for request in self.requests:
            if request["methodName"] != method_name:
                continue

            if dynamic:
                request["javascriptPath"] = request_object
                request.pop("blob", None)
            elif request_object is not None:
                request["blob"] = request_object["requestValue"]["blob"]
            self.steps += [{"requestName": request["name"]}]
            return request["name"]

    def add_request_from_file(
        self, endpoint: _Endpoint, method_name: str, request_file: str
    ) -> str:
        """
        Adds the request in the specified file to the corresponding endpoint and method.

        Args:
            endpoint: The endpoint object associated with the request
            method_name: The name of the method that this request will be hitting
            request_file: The path to the file containing the request information
        """
        _, file_ext = os.path.splitext(request_file)

        try:
            with open(request_file) as file:
                file_contents = file.read()
        except:
            raise Exception(f"failed to open file: {request_file}")
        # pylint: disable=duplicate-code
        dynamic = False

        if file_ext == ".json":
            data = json.loads(file_contents)
        elif file_ext in [".yaml", ".yml"]:
            data = yaml.safe_load(file_contents)
        elif file_ext == ".js":
            dynamic = True
            data = request_file
        else:
            raise Exception(
                f"unsupported file format: {file_ext}. Only JSON, YAML, and JS are supported"
            )

        return self.add_request(endpoint, method_name, data, dynamic)

    def add_assert_equal(self, value_name: str, expected_value: str):
        """
        Adds an assert equal given the value expression and expected value

        Args:
            value_name: The name of the value to assert
            expected_value: The expected value
        """
        assertion = f'requests.{value_name} == "{expected_value}"'
        self.steps.append({"asserts": assertion})

    def add_assert_v1(
        self,
        assert_value: str = "",
        assert_expected_value: str = "",
        assert_unexpected_value: str = "",
        assert_step: _Assert = None,
        max_retries: int = 0,
        interval: str = "",
        until: str = "",
        assert_step_name: str = "",
        description: str = "",
        ignore: bool = False,
        break_: bool = False,
        if_: str = "",
    ):
        """
        Adds an assert given the value expression and expected value

        Args:
            assert_value: The name of the value to assert
            assert_expected_value: The expected value
            assert_unexpected_value: The unexpected value
            assert_step: The assert step
            max_retries: The maximum number of retries
            interval: The interval between retries
            until: The condition to stop retrying
            assert_step_name: Assert step name used by the code
                              generation to support assert override
            description: The description of the assert step
            ignore: If set, a failure will not break out of the scenario
            break_: If set, will break out of the test after the assert (for debugging)
            if_: If condition for executing this assert
        """
        if assert_step is not None:
            self.steps_v1.append(
                _Step(
                    assert_step,
                    max_retries,
                    interval,
                    until,
                    ignore=ignore,
                    break_=break_,
                    if_=if_,
                )
            )
        else:
            assert_step = _Assert(
                assert_value=assert_value,
                assert_expected_value=assert_expected_value,
                assert_unexpected_value=assert_unexpected_value,
                assert_step_name=assert_step_name,
                description=description,
            )
            self.steps_v1.append(
                _Step(
                    assert_step,
                    max_retries,
                    interval,
                    until,
                    ignore=ignore,
                    break_=break_,
                    if_=if_,
                )
            )

    def _build_metadata_for_endpoint(self, endpoint: _Endpoint):
        if endpoint.endpoint in self.endpoints:
            return

        self.services += endpoint.services

        self.endpoints.append(endpoint.endpoint)

        mock_description_yaml = yaml.dump(endpoint.mock_description)

        func = _library.buildRequestsWrapper
        argtypes = [ctypes.c_char_p]
        restype = ctypes.c_char_p

        requests = _call_function(
            func,
            argtypes,
            restype,
            [mock_description_yaml.encode()],
            return_output=True,
        )

        parsed_requests = json.loads(requests)
        self.requests.append(parsed_requests[0])

    def set_global_headers(self, headers):
        """
        Sets the global headers for this scenario
        """
        self.global_headers = headers

    # pylint: disable=too-many-locals
    def add_request_v1(
        self,
        request: _Request,
        max_retries: Optional[int] = 0,
        interval: Optional[str] = "",
        until: Optional[str] = "",
        until_expected_code: Optional[int] = None,
        until_unexpected_code: Optional[int] = None,
        path_override: Optional[dict] = None,
        query_override: Optional[dict] = None,
        form_override: Optional[dict] = None,
        vars_override: Optional[dict] = None,
        blob_override: Optional[dict] = None,
        blob_removal: Optional[List[str]] = None,
        description: str = "",
        step_name: str = "",
        ignore: bool = False,
        break_: bool = False,
        if_: str = "",
        export: Optional[dict] = None,
        until_func: Optional[str] = None,
        wait: str = "",
        with_: str = "",
        expected_code: Optional[int] = 0,
        unexpected_code: Optional[int] = 0,
    ) -> _Step:
        """
        Adds a request to this scenario.

        Args:
            request: request information
            max_retries: The maximum number of retries
            interval: The interval between retries
            until: The condition to stop retrying
            ignore: If set, a failure will not break out of the scenario
            break_: If set, will break out of the test after the request (for debugging)
            if_: If condition for executing this request
            until_func: The repeat function to use for this step
        Returns:
            The name of the step that was added
        """
        if until_expected_code is not None and until_expected_code != 0:
            until = f"code == {until_expected_code}"
        elif until_unexpected_code is not None and until_unexpected_code != 0:
            until = f"code != {until_unexpected_code}"

        step = _Step(
            request,
            max_retries,
            interval,
            until,
            vars_override=vars_override,
            path_override=path_override,
            query_override=query_override,
            form_override=form_override,
            blob_override=blob_override,
            blob_removal=blob_removal,
            description=description,
            step_name=step_name,
            ignore=ignore,
            break_=break_,
            if_=if_,
            export=export,
            until_func=until_func,
            wait=wait,
            with_=with_,
            expected_code=expected_code,
            unexpected_code=unexpected_code,
        )

        self.steps_v1.append(step)
        return step

    # pylint: disable=too-many-locals
    def add_scenario_v1(
        self,
        scenario:  Self,
        max_retries: int = 0,
        interval: str = "",
        until: str = "",
        vars_override: Optional[dict]=None,
        description: Optional[str]="",
        step_name: str='',
        break_: bool=False,
        ignore: bool = False,
        if_: str = "",
        export: Optional[dict]=None,
        wait: str="",
    ) -> _Step:
        """
        Adds a scenario to this scenario.

        Args:
            scenario: scenario information
        Returns:
            The name of the step that was added
        """
        # pylint: disable=line-too-long
        step = _Step(
            step=scenario,
            max_retries=max_retries,
            interval=interval,
            until=until,
            vars_override=vars_override,
            description=description,
            step_name=step_name,
            break_=break_,
            ignore=ignore,
            if_=if_,
            export=export,
            wait=wait,)
        self.steps_v1.append(step)
        return step

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        # Helper function to handle the repeat dictionary creation
        def get_repeat_dict(step_v1):
            return {
                "maxRetries": step_v1.max_retries,
                "interval": step_v1.interval,
                "until": step_v1.until,
                "untilPython": textwrap.dedent(inspect.getsource(step_v1.until_func))
                if step_v1.until_func else None,
                "untilPythonFuncName": step_v1.until_func.__name__
                if step_v1.until_func else "",
                "with": step_v1.with_
            }

        # Helper function to handle common step attributes
        def add_common_step_attributes(step_v1, step):
            attributes = {
                "override": step_v1.vars_override if step_v1.vars_override
                is not None else step_v1.response_value,
                                "blobOverride": step_v1.blob_override,
                "blobRemoval": step_v1.blob_removal,
                "name": step_v1.step_name,
                "description": step_v1.description,
                "cookies": step_v1.cookie_value,
                "if": step_v1.if_,
                "export": step_v1.export,
                "wait": step_v1.wait,
            }
            # Add attributes that are not None or empty string
            step.update({k: v for k, v in attributes.items() if v not in [None, ""]})

            if step_v1.expected_code != 0:
                step["expectedCode"] = step_v1.expected_code
            if step_v1.unexpected_code != 0:
                step["unexpectedCode"] = step_v1.unexpected_code
            if step_v1.path_override is not None:
                step["pathOverride"] = step_v1.path_override
            if step_v1.query_override is not None:
                step["queryOverride"] = step_v1.query_override
            if step_v1.form_override is not None:
                step["formOverride"] = step_v1.form_override

        steps = []
        for step_v1 in self.steps_v1:
            step = {}

            if isinstance(step_v1.step, (_Assert, _Request)):
                step = step_v1.step.to_json()

            if isinstance(step_v1.step, (_Request, _Scenario)):
                repeat = get_repeat_dict(step_v1)
                if any(repeat.values()):
                    step["repeat"] = {k: v for k, v in repeat.items() if v not in [None, ""]}

            if isinstance(step_v1.step, _Scenario):
                step["scenarioName"] = step_v1.step.name

            add_common_step_attributes(step_v1, step)
            steps.append(step)

        scenario_dict = {
            "name": self.name,
            "steps": steps,
            "ignore": self.ignore,
        }

        # Add scenario level attributes if they are not None or empty string
        if self.vars not in [None, ""]:
            scenario_dict["vars"] = self.vars
        if self.headers not in [None, ""]:
            scenario_dict["headers"] = self.headers

        return scenario_dict

    def get_async_var(self, var_name):
        """
        construct backend interpretation of accessing scenario vars
        """
        return f"vars.{var_name}"

    def get_async_request_value(self, request, path):
        """
        returns request's response value construct for asynchronous backend
        """
        return f"requests.{request.name}.res.{path}"

    def get_async_scenario_value(self, scenario, var):
        """
        returns scenario's response value construct for asynchronous backend
        """
        return f"scenarios.{scenario.name}.{var}"

    def request_status_check(self, request, code):
        """
        returns if construct for asynchronous backend
        """
        return f"requests.{request.name}.code == {code}"
