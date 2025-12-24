"""
Contains helpers for executing Skyramp tests
"""

import itertools
import time


# given list of mocks  we permutate them and execute given test scenario
# pylint: disable=too-many-locals
def _execute_component_test(client,
                            mocks_dict,
                            scenario,
                            global_vars=None,
                            debug=False,
                            wait_time=5):
    # generate combinations
    responses = []
    index_list = list(range(len(mocks_dict)))

    keys = list(mocks_dict.keys())
    values = list(mocks_dict.values())
    for i in range(1, len(mocks_dict) + 1):
        combinations = itertools.combinations(index_list, i)

        for combination in combinations:
            delim = ", "
            title = [keys[idx] for idx in combination]
            responses = [item for idx in combination for item in values[idx]]
            print("mocking", delim.join(title))

            client.mocker_apply(response=responses)
            time.sleep(wait_time)

            result = client.tester_start(
                scenario=scenario,
                test_name=scenario.name,
                blocked=True,
                global_vars=global_vars,
            )
            print("Result of tests:", result.passed())
            if debug:
                print(result)
            print()
