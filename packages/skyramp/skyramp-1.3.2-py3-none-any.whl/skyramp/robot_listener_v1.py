''' Robot Framework listener that allows adding test cases to the suite'''
from __future__ import print_function
from robot.libraries.BuiltIn import BuiltIn

class RobotListenerV1():
    ''' Robot Framework listener that allows adding test cases to the suite'''
    ROBOT_LISTENER_API_VERSION = 3
    ROBOT_LIBRARY_SCOPE = "TEST SUITE"

    def __init__(self):
        # pylint: disable=invalid-name
        self.ROBOT_LIBRARY_LISTENER = self
        self.current_suite = None

    # pylint: disable=unused-argument
    def _start_suite(self, suite, result):
        # save current suite so that we can modify it later
        BuiltIn().set_global_variable("${listenerType}", "RobotListenerV1")
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
        test_case= self.current_suite.tests.create(name=name)
        # test_case.keywords.create(name=kwname, args=args) #deprecated in 4.0
        test_case.body.create_keyword(name=kwname, args=args)


# To get our class to load, the module needs to have a class
# with the same name of a module. This makes that happen:
globals()[__name__] = RobotListenerV1
