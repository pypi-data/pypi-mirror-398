"""
Defines a Skyramp local client
"""

from typing import Optional, Union, List

from skyramp.client_base import _ClientBase
from skyramp.scenario import _Scenario
from skyramp.test_load_config import _LoadTestConfig
from skyramp.test_request import _Request
from skyramp.test_status import TestStatus
from skyramp.test_status_interactive_mode import TestStatusV3
from skyramp.test_status import ResponseLog

class _LocalClient(_ClientBase):
    """ This class contains methods to execute tests for local env """
    def __init__(self, framework: Optional[str] = None):
        super().__init__()
        self.framework = framework

    # pylint: disable=too-many-locals
    def tester_start(
        self,
        test_name: str,
        scenario: Union[_Scenario, List[_Scenario]],
        global_headers: Optional[map] = None,
        blocked: Optional[bool] = False,
        global_vars: Optional[map] = None,
        override_code_path: Optional[str] = None,
        override_dict: Optional[dict] = None,
        endpoint_address: Optional[str or dict] = None,
        pip_requirements: Optional[str] = None,
        skip_verify: Optional[bool] = None,
        blobs: Optional[dict] = None,
        is_formatting_enabled: bool = False,
        loadtest_config: Optional[_LoadTestConfig] = None,
        deploy_worker: Optional[bool] = False,
        override_labels: Optional[map] = None,
        **kwargs,
    ) -> TestStatus:
        # flag to bring up worker in docker network
        status = super().tester_start_v1(scenario, global_headers, "",
                 "", test_name, blocked,
                 global_vars, "", "", "", override_code_path,
                 override_dict, endpoint_address,
                 pip_requirements, skip_verify=skip_verify,
                 blobs=blobs,
                 is_formatting_enabled=is_formatting_enabled,
                 loadtest_config=loadtest_config,
                 override_labels=override_labels,
                 **kwargs)
        return status

    def execute_request(self, request: _Request,
        skip_verify: Optional[bool] = None,
        global_vars: Optional[map] = None,
        **kwargs,
    ) -> ResponseLog:
        return super()._execute_request(
                 request,
                 "",
                 skip_verify=skip_verify,
                 global_vars=global_vars,
                 **kwargs
                 )

    def execute_scenario(
        self,
        scenario: _Scenario,
        global_headers: Optional[map] = None,
        blocked: Optional[bool] = True,
        global_vars: Optional[map] = None,
        override_code_path: Optional[str] = None,
        override_dict: Optional[dict] = None,
        endpoint_address: Optional[str] = None,
        pip_requirements: Optional[str] = None,
        skip_verify: Optional[bool] = None,
        blobs: Optional[dict] = None,
        is_formatting_enabled: bool = False,
        loadtest_config: Optional[_LoadTestConfig] = None,
        override_labels: Optional[map] = None,
        **kwargs,
    ) -> TestStatusV3:
        return super()._execute_scenario(scenario.name,
                  scenario,
                  global_headers,
                  "",
                  "",
                  blocked,
                  global_vars,
                  "",
                  "",
                  "",
                  override_code_path,
                  override_dict=override_dict,
                  endpoint_address=endpoint_address,
                  pip_requirements=pip_requirements,
                  skip_verify=skip_verify,
                  blobs=blobs,
                  is_formatting_enabled=is_formatting_enabled,
                  loadtest_config=loadtest_config,
                  override_labels=override_labels,
                  **kwargs)

    def get_tester_status(
        self,
        tester_id,
        blocked: Optional[bool] = False,
        is_formatting_enabled: Optional[bool] = False,
        **kwargs,
    ) -> TestStatus:
        return None
