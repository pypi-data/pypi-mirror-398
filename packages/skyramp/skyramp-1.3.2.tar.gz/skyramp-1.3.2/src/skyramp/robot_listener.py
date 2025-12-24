""" Robot Framework listener to add test cases to the current suite """

import json
import os
from robot.api.deco import keyword
from robot.libraries.BuiltIn  import BuiltIn
from skyramp.test_status import TesterStatusType, TestResultType
from skyramp.deprecated_status import TestStatusV1


class RobotListener:
    """
    Robot Framework listener
    """

    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"
    index = 0
    test_case_list = []

    def __init__(self):
        # pylint: disable=invalid-name
        self.ROBOT_LIBRARY_LISTENER = self
        self.current_suite = None

    # pylint: disable=unused-argument
    def _start_suite(self, suite, result):
        self.current_suite = suite

    def add_test_case(self, name, kwname, *args):
        """Adds a test case to the current suite

        'name' is the test case name
        'kwname' is the keyword to call
        '*args' are the arguments to pass to the keyword

        Example:
            add_test_case  Example Test Case
            ...  log  hello, world  WARN
        """
        test_case = self.current_suite.tests.create(name=name)
        test_case.body.create_keyword(name=kwname, args=args)

    def run_test_cases(
        self, file_path, address, override_code_path, global_vars, endpoint_addr
    ):
        """
        Executes the test cases in file_path
        """
        library = self._get_library_from_file(file_path)
        if isinstance(global_vars, dict) is False:
            global_vars = dict(json.loads((global_vars)))
        if endpoint_addr == "":
            self.test_case_list = library.execute_tests(
                address=address,
                override_code_path=override_code_path,
                global_vars=global_vars,
            )
        else:
            self.test_case_list = library.execute_tests(
                address=address,
                override_code_path=override_code_path,
                global_vars=global_vars,
                endpoint_address=endpoint_addr,
            )
        is_version_v1 = isinstance(self.test_case_list, TestStatusV1)
        for test_case in self.test_case_list:
            if len(test_case) > 0 and test_case[0].type == TestResultType.Scenario:
                continue
            if is_version_v1:
                self.add_test_case(
                    test_case[0].test_case_name, "Keyword To Execute", test_case
                )
            else:
                self.add_test_case(test_case[0].name, "Log Scenario Status", "")
        self.current_suite.filter(excluded_tags="placeholder")

    def run_test_cases_v1(self, address, override_code_path, global_vars, **args):
        """
        Executes the test cases in file_path and supporting args
        """
        file_path = BuiltIn().get_variable_value("${SKYRAMP_TEST_FILE}")
        library = self._get_library_from_file(file_path)
        if args is not None:
            self.test_case_list = library.execute_tests(
                address, override_code_path, global_vars, **args
            )
        else:
            self.test_case_list = library.execute_tests(
                address, override_code_path, global_vars
            )
        self._process_output()

    def run_test_cases_v2(self, address, override_code_path, global_vars, **args):
        """
        Executes the test cases in file_path and supporting args
        """
        file_path = BuiltIn().get_variable_value("${SKYRAMP_TEST_FILE}")
        library = self._get_library_from_file(file_path)
        if args is not None:
            self.test_case_list = library.execute_tests(
                address, override_code_path, global_vars, **args
            )
        else:
            self.test_case_list = library.execute_tests(
                address, override_code_path, global_vars
            )
        self._process_output_v2()

    def _process_output(self):
        """Process output"""
        is_version_v1 = isinstance(self.test_case_list, TestStatusV1)
        for test_case in self.test_case_list:
            if is_version_v1:
                self.add_test_case(
                    test_case[0].test_case_name, "Keyword To Execute", test_case
                )
            else:
                self.add_test_case(test_case[0].name, "Log Scenario Status", "")

    def _process_output_v2(self):
        """
        Process output
        we flatten scenarios into a list of request
        this assumes each request step has expected code
        """

        new_list = []
        for test_case in self.test_case_list:
            past_step = None
            repeat = []
            for result in test_case:
                if result.type == "scenario":
                    continue
                if (result.step_name != "" and
                        past_step is not None and result.step_name == past_step.step_name):
                    repeat.append(result)
                    past_step = result
                    continue
                if past_step is not None and past_step.step_name != result.step_name:
                    if len(repeat) != 0:
                        new_list.append(repeat)
                        repeat = []
                    else:
                        new_list.append(past_step)
                past_step = result
            # handle last item
            if len(repeat) != 0:
                new_list.append(repeat)
            else:
                new_list.append(past_step)

        for test_case in new_list:
            if isinstance(test_case, list):
                self.add_test_case(test_case[0].step_name, "Log Request Status", test_case)
            else:
                self.add_test_case(test_case.step_name, "Log Request Status", test_case)

    def _get_library_from_file(self, file_path):
        """Get library from file"""
        base_file = os.path.basename(file_path)
        return BuiltIn().get_library_instance(name=base_file.replace(".py", ""))

    @keyword
    def log_scenario_status(self, test):
        """Log scenario status"""
        test_results = self.test_case_list[self.index]
        for test_case in test_results[1:]:
            BuiltIn().run_keyword("Log Test Data", test_case)
        self.index += 1
        if test_results[0].error != "":
            BuiltIn().fail(test_results[0])
        elif test_results[0].status == TesterStatusType.Skipped:
            BuiltIn().skip(test_results[0])

    @keyword
    def log_request_status(self, test):
        """Log request status"""
        if isinstance(test, list):
            if test[-1].error != "" or test[-1].status == TesterStatusType.Failed:
                BuiltIn().fail(test[-1])
            elif test[-1].status == TesterStatusType.Skipped:
                BuiltIn().skip(test[-1])
            for repeat in test:
                BuiltIn().run_keyword("Log Test Data", repeat)
        else:
            BuiltIn().log(message=test.to_html(), html=True)
            if test.error != "":
                BuiltIn().fail(test)
            elif test.status == TesterStatusType.Skipped:
                BuiltIn().skip(test)

    @keyword
    def log_test_data(self, test_case):
        """Log test data"""
        BuiltIn().log(message=test_case.to_html(), html=True)

    @keyword
    def keyword_to_execute(self, test_case):
        """Keyword to execute"""
        if test_case[0].test_case_status != "[]":
            BuiltIn().fail(test_case)
        elif test_case[0].status == TesterStatusType.Skipped:
            BuiltIn().skip(test_case)
        else:
            BuiltIn().log(test_case)
