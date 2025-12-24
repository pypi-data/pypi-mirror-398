""" This module contains the robot test suite runner """

import os
from robot import run


ROBOT_CONTENT = """
*** Variables ***
${ADDRESS}    localhost:35142
${OVERRIDE_CODE_PATH}    
${GLOBAL_VARS}      {}
${ENDPOINT_ADDRESS}      
${SKYRAMP_TEST_FILE}

*** Settings ***
Library           skyramp.RobotListener
Library           ${SKYRAMP_TEST_FILE}

*** Test Cases ***
Skyramp Tests
    Run Test Cases V1      ${ADDRESS}   ${OVERRIDE_CODE_PATH}  ${GLOBAL_VARS}
"""
SKYRAMP_ROBOT_FILE_NAME = "skyramp_tests.robot"


def run_robot_test_suite(robot_file="", variable=None, output_dir=None, name=None):
    """
    Run the robot test suite
    :param robot_file: The robot file to run
    :param variable: The variables to pass to the robot file
    :param output_dir: The output directory to store the robot report
    """
    robot_path = robot_file
    if robot_path == "":
        robot_path = SKYRAMP_ROBOT_FILE_NAME
        if not os.path.exists(robot_path):
            with open(robot_path, "w") as file:
                file.write(ROBOT_CONTENT)

    # Create output directory if it does not exist
    if output_dir is not None:
        # Convert the relative path to an absolute path
        output_dir = os.path.abspath(output_dir)
        # Check if the directory exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    run(robot_path, variable=variable, outputdir=output_dir, name=name)
