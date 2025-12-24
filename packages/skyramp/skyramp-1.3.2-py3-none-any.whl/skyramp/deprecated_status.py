""" Deprecated status module for Skyramp """
import json
from skyramp.test_status import TestStatus, RawTestResult

class TestStatusV1(TestStatus):
    """
    TestStatusV1 object
    """

    def __init__(self, options: dict):
        self.test_results = []
        self.tester_id = options.get("tester_id", "")
        results = options.get("test_results", [])
        # iterate over the results and create RawTestResult objects
        if len(results) > 0 and "results" in results and len(results["results"]) > 0:
            for test_result in results["results"][1:]:
                result = RawTestResult(test_result)
                result_list = []
                # if the result is an assert, add it to the previous result
                if result.name == "assert":
                    result_list = self.test_results.pop()
                # merge all the repeat request into one test case
                if (
                    ".repeat." in result.description
                    and ".repeat.0" not in result.description
                ):
                    result_list = self.test_results.pop()

                # if first result in the result_list update the test case name, status and error
                if len(result_list) == 0:
                    result.test_case_name = result.step_name
                    if result.step_name == "":
                        result.test_case_name = result.name
                # add the result to the result_list
                result_list.append(result)

                if result.error != "":
                    self.pass_status = False
                    data = json.loads(result_list[0].test_case_status)
                    data.append(result.error)
                    result_list[0].test_case_status = json.dumps(data)
                # update the test_results list
                self.test_results.append(result_list)

    def __repr__(self):
        return f"TestStatusV1(test_results={self.test_results})"
