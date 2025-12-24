"""
TestStatus module
"""

from typing import List
import ctypes
import json
from abc import ABC
from skyramp.utils import _library, _call_function, convert_time_to_milliseconds


class TesterStatusType:
    """
    TesterStatusType object
    """

    Idle = "idle"
    Initializing = "initializing"
    Waiting = "waiting"
    Running = "running"
    Failed = "failed"
    Skipped = "skipped"
    Stopping = "stopping"
    Stopped = "stopped"
    Finished = "finished"


class TestResultType:
    """
    TestResultType object
    """

    NoneType = ""
    Command = "command"
    Request = "request"
    Scenario = "scenario"
    Load = "load"
    Repeat = "repeat"
    Assert = "assert"
    With = "with"


class TestTimeseriesStat:
    """
    TestTimeseriesStat object
    """

    timestamp: str = ""
    error_rate: str = ""
    rps: str = ""
    avg_latency: str = ""
    total_count: int = 0

    def __init__(self, options: dict):
        if "timestamp" in options:
            self.timestamp = convert_time_to_milliseconds(options["timestamp"])
        if "errorRate" in options:
            self.error_rate = f"{round(options['errorRate'], 4)}"
        if "RPS" in options:
            self.rps = f"{round(options['RPS'], 4)}"
        if "avgLatency" in options:
            self.avg_latency = convert_time_to_milliseconds(options["avgLatency"])
        if "totalCount" in options:
            self.total_count = options["totalCount"]

    def __repr__(self):
        _data = {
            "timestamp": self.timestamp,
            "error_rate": self.error_rate,
            "rps": self.rps,
            "avg_latency": self.avg_latency,
            "total_request_count": self.total_count,
        }
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != ""}
        if "scenarioStats" in filtered_data:
            del filtered_data["scenarioStats"]
        return f"TimeseriesStat({json.dumps(filtered_data)})"


class TestStat:
    """
    TestStat object
    """

    description: str = ""
    count: int = 0
    executed: int = 0
    fail: int = 0
    avg_latency: str = ""
    max_latency: str = ""
    min_latency: str = ""
    p99th_latency: str = ""
    p95th_latency: str = ""
    p90th_latency: str = ""
    code_table: dict = None
    log_table: dict = None
    type: TestResultType = ""
    id: str = ""
    assert_statement: str = ""

    def __init__(self, options: dict):
        self.description = options.get("Description", "")
        self.count = options.get("Count", 0)
        self.executed = options.get("Executed", 0)
        self.fail = options.get("Fail", 0)
        self.avg_latency = options.get("AvgLatency", "")
        self.max_latency = options.get("MaxLatency", "")
        self.min_latency = options.get("MinLatency", "")
        self.p99th_latency = options.get("L99thLatency", "")
        self.p95th_latency = options.get("L95thLatency", "")
        self.p90th_latency = options.get("L90thLatency", "")
        self.code_table = options.get("CodeTable", {})
        self.log_table = options.get("LogTable", {})
        self.type = options.get("Type", "")
        self.id = options.get("id", "")
        self.assert_statement = options.get("AssertStatement", "")

    def to_json(self):
        """
        Returns the TestStat object as a JSON
        """
        _data = {
            "description": self.description,
            "count": self.count,
            "executed": self.executed,
            "fail": self.fail,
            "avg_latency": convert_time_to_milliseconds(self.avg_latency),
            "max_latency": convert_time_to_milliseconds(self.max_latency),
            "min_latency": convert_time_to_milliseconds(self.min_latency),
            "p99th_latency": convert_time_to_milliseconds(self.p99th_latency),
            "p95th_latency": convert_time_to_milliseconds(self.p95th_latency),
            "p90th_latency": convert_time_to_milliseconds(self.p90th_latency),
            "code_table": self.code_table,
            "log_table": self.log_table,
            "assert_statement": self.assert_statement,
        }
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != "" and v != {}}
        return filtered_data

    def get_stats(self):
        """
        Returns the TestStat object as a JSON
        """
        stat = self.to_json()
        stat.pop("log_table", None)
        stat.pop("code_table", None)
        return stat

    def __repr__(self):
        return f"Stats({json.dumps(self.to_json(), indent=2)})"


class RequestLog:
    """
    RequestLog object
    """

    path: str = ""
    method: str = ""
    headers: dict = {}
    cookies: dict = {}
    payload: str = ""
    test_group_id: str = ""

    def __init__(self, options: dict):
        for key in ["path", "method", "headers", "cookies", "payload"]:
            if key in options:
                setattr(self, key, options[key])

    def __repr__(self):
        _data = {
            "path": self.path,
            "method": self.method,
            "headers": self.headers,
            "cookies": self.cookies,
            "payload": self.payload,
            "test_group_id": self.test_group_id,
        }
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != ""}
        return f"RequestLog({json.dumps(filtered_data, indent=2)})"


class TesterState:
    """
    TesterState object
    """

    vars: dict = {}
    scenario_vars: dict = {}
    exports: dict = {}
    blob_overrides: dict = {}

    def __init__(self, options: dict):
        if "vars" in options:
            self.vars = options["vars"]
        if "scenarioVars" in options:
            self.scenario_vars = options["scenarioVars"]
        if "exports" in options:
            self.exports = options["exports"]
        if "blobOverrides" in options:
            self.blob_overrides = options["blobOverrides"]

    def __repr__(self):
        _data = {
            "vars": self.vars,
            "scenario_vars": self.scenario_vars,
            "exports": self.exports,
            "blob_overrides": self.blob_overrides,
        }
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != ""}
        return f"TesterState({json.dumps(filtered_data, indent=2)})"


class ResponseLog:
    """
    ResponseLog object
    """

    status_code: int = 0
    headers: dict = {}
    cookies: dict = {}
    payload: str = ""

    def __init__(self, options: dict):
        if "statusCode" in options:
            self.status_code = options["statusCode"]
        if "headers" in options:
            self.headers = options["headers"]
        if "cookies" in options:
            self.cookies = options["cookies"]
        if "payload" in options:
            self.payload = options["payload"]

    def get_payload(self, key):
        """
        Returns the payload value for the given key
        """
        if key is None:
            return json.loads(self.payload)
        keys = key.split(".")
        value = json.loads(self.payload)
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, None)
            else:
                return None
        return value

    def __repr__(self):
        _data = {
            "status_code": self.status_code,
            "headers": self.headers,
            "cookies": self.cookies,
            "payload": self.payload,
        }
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != ""}
        return f"ResponseLog({json.dumps(filtered_data, indent=2)})"

class RawTestResult:
    """
    RawTestResult object
    Sent from Skyramp worker
    """
    name: str = ""
    status: str = ""
    description: str = ""
    nested_info: str = ""
    step_description: str = ""
    step_name: str = ""
    parent: str = ""
    executed: bool = None
    error: str = ""
    input: RequestLog = None
    output: ResponseLog = None
    type: TestResultType = ""
    begin: int = None
    end: int = None
    duration: int = None
    timeseries: List[TestTimeseriesStat] = None
    stat: TestStat = None
    state: TesterState = None
    test_case_status: json = "[]"
    test_case_name: str = ""
    id: str = ""

    # pylint: disable=too-many-branches
    def __init__(self, options: dict):
        if "name" in options:
            self.name = options["name"]
        if "status" in options:
            self.status = options["status"]
        if "description" in options:
            self.description = options["description"]
        if "nestedInfo" in options:
            self.nested_info = options["nestedInfo"]
            self.id = options["nestedInfo"]
        if "stepDescription" in options:
            self.step_description = options["stepDescription"]
        if "stepName" in options:
            self.step_name = options["stepName"]
        if "parent" in options:
            self.parent = options["parent"]
        if "executed" in options:
            self.executed = options["executed"]
        if "error" in options:
            self.error = options["error"]
        if "input" in options:
            if options["input"] is not None and "service" in options["input"]:
                options["input"]["service"] = None
            self.input = options["input"]
        if "output" in options:
            self.output = options["output"]
        if "type" in options:
            self.type = options["type"]
        if "begin" in options:
            self.begin = options["begin"]
        if "end" in options:
            self.end = options["end"]
        if "duration" in options and options["duration"] != 0:
            self.duration = options["duration"]
        if "timeseries" in options and options["timeseries"] != []:
            self.timeseries = options["timeseries"]
        if "stat" in options:
            self.stat = options["stat"]
        if "state" in options:
            self.state = options["state"]

    def __str__(self):
        _data = {
            "name": self.name,
        }
        if self.status:
            _data["status"] = self.status
        if self.description:
            _data["description"] = self.description
        if self.step_description:
            _data["step_description"] = self.step_description
        if self.step_name:
            _data["step_name"] = self.step_name
        if self.error:
            _data["error"] = self.error
        return f"TestResult({json.dumps(_data, indent=2)})"

    def __repr__(self):
        _data = {
            "name": self.name,
            "status": self.status,
            "description": self.description,
            "nested_info": self.nested_info,
            "step_description": self.step_description,
            "step_name": self.step_name,
            "parent": self.parent,
            "executed": self.executed,
            "error": self.error,
            "request": self.input,
            "response": self.output,
            "type": self.type,
            "begin": self.begin,
            "end": self.end,
            "duration": self.duration,
            "timeseries": self.timeseries,
            "stat": self.stat,
            "state": self.state,
            "test_case_status": self.test_case_status,
        }
        _data["test_case_status"] = None
        filtered_data = {k: v for k, v in _data.items() if v is not None and v != ""}
        return f"TestResult({json.dumps(filtered_data, indent=2)})"

    def to_html(self):
        """
        Returns HTML text representation of the test status
        """
        html_content = "<div>\n"
        html_content += _html_entry("Step Name", self.name)
        html_content += _html_entry("Step Description", self.step_description)
        if self.error:
            html_content += _html_entry("Error", self.error)
        if self.input:
            html_content += _html_entry("Request", json.dumps(self.input, indent=2))
        if self.output:
            html_content += _html_entry("Response", json.dumps(self.output, indent=2))
        if self.stat:
            html_content += _html_entry("Stat", self.stat)
        if self.state:
            html_content += _html_entry("State", json.dumps(self.state, indent=2))
        if self.timeseries:
            html_content += _html_entry("Timeseries", self.timeseries)
        if self.duration:
            html_content += _html_entry("Duration", self.duration)
        if self.type:
            html_content += _html_entry("Type", self.type)
        if self.begin:
            html_content += _html_entry("Begin", self.begin)
        if self.end:
            html_content += _html_entry("End", self.end)
        html_content += _html_entry("Status", self.status)
        html_content += "</div>\n\n"
        return html_content


def _filtered(data: dict):
    return {k: v for k, v in data.items() if v is not None and v != ""}


def _html_entry(title, data):
    return f"<span><strong>{title}:</strong> {data}</span>\n"


class TestStatus(ABC):
    """
    TestStatus object
    """
    tester_id =""
    test_results: List[List[RawTestResult]] = []
    pass_status: bool = True
    index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.test_results):
            result = self.test_results[self.index]
            self.index += 1
            return result
        raise StopIteration

    def __getitem__(self, index):
        return self.test_results[index]

    def __len__(self):
        return len(self.test_results)

    def passed(self):
        """
        Returns True if all the tests passed
        """
        return self.pass_status

    def failed(self):
        """
        Returns True if any of the tests failed
        """
        failed_json = []
        for result in self.test_results:
            for step in result:
                if step.status == TesterStatusType.Failed and step.error != "":
                    failed_json.append(
                        {
                            "name": step.name,
                            "step_description": step.step_description,
                            "request": step.input,
                            "response": step.output,
                            "status": step.status,
                            "error": step.error,
                        }
                    )
        return json.dumps(failed_json, indent=2)

class TestStatusV2(TestStatus):
    """
    TestStatusV2 object
    """

    def __init__(self, options: dict):
        self.test_results = []
        self.tester_id = options.get("tester_id", "")
        results = options.get("test_results", [])
        for result in results:
            scenario_data = []
            for step in result:
                test_result = RawTestResult(step)
                if test_result.error != "":
                    self.pass_status = False
                scenario_data.append(test_result)
            self.test_results.append(scenario_data)

    def __repr__(self):
        return f"TestStatusV2(test_results={self.test_results})"

class TestResult:
    """
    Test result object for synchronous execution
    """
    url: str = ""
    method: str = ""
    status_code: int =0
    request_headers: dict = {}
    request_cookies: dict = {}
    request_body_raw: str = ""
    request_body_dict: dict = {}
    response_headers: dict = {}
    response_cookies: dict = {}
    response_body_raw: str = ""
    response_body_dict: dict = {}

    def __init__(self, raw: RawTestResult):
        if raw.input is not None:
            request = raw.input
            if "path" in request:
                self.url = request["path"]
            if "method" in request:
                self.method: request["method"]
            if "headers" in request:
                self.request_headers = request["headers"]
            if "cookies" in request:
                self.request_cookies = request["cookies"]
            if "payload" in request:
                self.request_body_raw = request["payload"]
                self.request_body_dict = json.loads(request["payload"])

        if raw.output is not None:
            response = raw.output
            if "statusCode" in response:
                self.status_code = response["statusCode"]
            if "headers" in response:
                self.response_headers = response["headers"]
            if "cookies" in response:
                self.response_cookies = response["cookies"]
            if "payload" in response:
                self.response_body_raw = response["payload"]
                self.response_body_dict = json.loads(response["payload"])

    def get_response_value(self, json_path=""):
        """
        Returns the response payload value for the given json path
        """
        if json_path is None:
            return self.response_body_dict

        if self.response_body_raw == "":
            return None

        func = _library.getJsonValue
        argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
        ]
        restype = ctypes.c_char_p
        args = [self.response_body_raw.encode(), json_path.encode()]

        ret = _call_function(func, argtypes, restype, args, True)

        if ret is None:
            return None

        return json.loads(ret)

    def __repr__(self):
        return f"TestResult({json.dumps(self.__dict__, indent=2)})"


def _get_response_value(response_body_raw, json_path):
    """
    Returns the response payload value for the given json path
    """
    if json_path is None or json_path == "":
        return json.loads(response_body_raw)

    if response_body_raw == "":
        return None

    func = _library.getJsonValue
    argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    restype = ctypes.c_char_p
    args = [response_body_raw.encode(), json_path.encode()]

    ret = _call_function(func, argtypes, restype, args, True)

    if ret is None:
        return None

    return json.loads(ret)
