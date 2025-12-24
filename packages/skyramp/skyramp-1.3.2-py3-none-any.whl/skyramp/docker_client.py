""" This class contains methods to manage Docker containers and volumes."""

import ctypes
from typing import Optional, Union, List

from skyramp.utils import _library, _call_function
from skyramp.client_base import _ClientBase
from skyramp.mock_object import _MockObject
from skyramp.scenario import _Scenario
from skyramp.response import _ResponseValue
from skyramp.test_load_config import _LoadTestConfig
from skyramp.test_request import _Request
from skyramp.test_status import TestStatus
from skyramp.test_status_interactive_mode import TestStatusV3
from skyramp.test_status import ResponseLog
from skyramp.traffic_config import _TrafficConfig
from skyramp.endpoint import ARGUMENT_TYPE
from skyramp.mock_v2 import MockV2

WORKER_URL = "public.ecr.aws/j1n2c2p2/rampup/worker"
WORKER_TAG = "latest"
VOLUME_NAME = "skyramp-worker"
CONTAINER_NAME = "skyramp"
CONTAINER_PORT = 35142


class WorkerInfoType(ctypes.Structure):
    """c type for worker info"""

    _fields_ = [
        ("container_name", ctypes.c_char_p),
        ("error", ctypes.c_char_p),
    ]


class _DockerClient(_ClientBase):
    port = None
    """ This class contains methods to manage Docker containers and volumes."""
    def __init__(self,
        worker_address: str="localhost:35142",
        network_name: str="",
        worker_url: str = WORKER_URL,
        worker_tag: str = WORKER_TAG,
        host_port: int = CONTAINER_PORT,
        service_alias: str ="",
        deploy_worker: bool = False,
        framework: str = "",
        worker_image: str = "",
        local_image: bool = False,
    ):
        if ":" in worker_address:
            self.port = int(worker_address.split(":")[1])
        super().__init__(worker_address=worker_address, network_name=network_name)
        self.network_name = network_name
        self.worker_address = worker_address
        self.framework = framework
        self.worker_image = worker_image
        self.local_image = local_image
        if deploy_worker:
            self.run_container(worker_url, worker_tag, host_port, service_alias)

    def run_container(
        self,
        worker_url: str = WORKER_URL,
        worker_tag: str = WORKER_TAG,
        host_port: int = CONTAINER_PORT,
        service_alias: str =""
    ):
        """
        Run a Docker container with the specified configuration.

        Args:
            worker_url (str): URL of the worker image.
            worker_tag (str): Tag of the worker image.
            container_port (int): Port to map to the container.

        Returns:
            docker.models.containers.Container: The running Docker container.

        Raises:
            Exception
            If an error occurs upon starting the docker container.

        """
        func = _library.newStartDockerSkyrampWorkerWrapper
        func.argtypes = ARGUMENT_TYPE
        func.restype = WorkerInfoType
        args = [
            worker_url.encode(),
            worker_tag.encode(),
            host_port,
            self.network_name.encode(),
            service_alias.encode(),
        ]
        result = func(*args)

        # the library should always return a result, but check just in case
        if not result:
            raise Exception(
                "Unexpected error occurred while starting the Docker container."
            )

        if result.error:
            error_msg = ctypes.c_char_p(result.error).value
            raise Exception(error_msg)

        if isinstance(result.container_name, bytes):
            # type checking for linter
            container_name = result.container_name.decode()
        elif result.container_name is None:
            # Should not happen that the container_name is None without error
            raise TypeError(
                "Unexpected result, neither error nor container name returned"
            )
        else:
            # If it's a type you didn't expect, handle the error
            raise TypeError(
                f"Unexpected type for container_name: {type(result.container_name)}"
            )
        return container_name

    def docker_down(self, container_name: str):
        """Stop and remove the Docker container."""
        func = _library.newDeleteDockerSkyrampWorkerWrapper
        argtypes = [ctypes.c_char_p]
        restype = ctypes.c_char_p

        err = _call_function(
            func,
            argtypes,
            restype,
            [container_name.encode()],
        )
        if err:
            raise Exception(err)

    def deploy_skyramp_worker(
        self,
        worker_image: Optional[str]='',
        host_port: Optional[int]=0
    ) -> None:
        """
        Run a Docker container with the specified configuration

        Args:
            worker_image (str): Repo:Tag of the worker image
            host_port (int): Port to bind worker's management port to host namespace

        Returns:
            docker.models.containers.Container: The running Docker container.

        Raises:
            Exception
            If an error occurs upon starting the docker container.
        """
        worker_url = WORKER_URL
        worker_tag = WORKER_TAG
        if worker_image != "":
            fields = worker_image.split(":")
            worker_url = fields[0]
            worker_tag = fields[1]
        if self.port != 0 and host_port == 0:
            port = self.port
        elif self.port == 0 and host_port == 0:
            port = CONTAINER_PORT
        else:
            port = host_port

        return self.run_container(worker_url, worker_tag, port)

    def delete_skyramp_worker(self, container_name: str) -> None:
        """
        Removes the Skyramp worker

        Args:
            worker_container_name: Container name of the Skyramp worker
        """
        self.docker_down(container_name)

    def mocker_apply(self,
        response: Union[_ResponseValue, List[_ResponseValue]] = None,
        mock_object: Optional[_MockObject] = None,
        traffic_config: Optional[_TrafficConfig] = None,
        **kwargs,
    ) -> None:
        """
        Applies mock configuration to worker in docker environment

        Args:
            response: The responses to apply to Mocker
            traffic_config: Traffic config
        """
        _ = kwargs.get("dummy")

        super().mocker_apply_v1(address=self.worker_address, response=response,
                                mock_object=mock_object, traffic_config=traffic_config)

    def apply_mock(
        self,
        mock: Union[MockV2, List[MockV2]],
    ) -> None:
        """
        Applies MockV2 configuration to worker in docker environment

        Args:
            mock: The MockV2 instance or list of MockV2 instances to apply
        """
        super().apply_mock(
            mock=mock,
        )

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
        container_name=None
        # flag to bring up worker in docker network
        if deploy_worker:
            docker_network = kwargs.get("docker_network")
            if docker_network is not None:
                self.network_name = docker_network
            worker_image = kwargs.get("worker_image")
            container_name=self.run_container(
                worker_url=worker_image.split(":")[0],
                worker_tag=worker_image.split(":")[1],
                host_port=self.port,
                service_alias=kwargs.get("docker_service_alias"),
            )
        status = super().tester_start_v1(scenario, global_headers, "",
                 self.worker_address, test_name, blocked,
                 global_vars, "", "", "", override_code_path,
                 override_dict, endpoint_address,
                 pip_requirements, skip_verify=skip_verify,
                 blobs=blobs,
                 is_formatting_enabled=is_formatting_enabled,
                 loadtest_config=loadtest_config,
                 override_labels=override_labels,
                 **kwargs)
        # cleanup the worker if it was deployed
        if deploy_worker and container_name is not None:
            self.docker_down(container_name)
        return status

    def execute_request(self, request: _Request,
        skip_verify: Optional[bool] = None,
        global_vars: Optional[map] = None,
        **kwargs,
    ) -> ResponseLog:
        return super()._execute_request(
                 request,
                 address=self.worker_address,
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
                  self.worker_address,
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
        return super()._get_tester_status(
            "",
            "",
            "",
            "",
            self.worker_address,
            tester_id,
            blocked=blocked,
            is_formatting_enabled=is_formatting_enabled,
            **kwargs,
        )
