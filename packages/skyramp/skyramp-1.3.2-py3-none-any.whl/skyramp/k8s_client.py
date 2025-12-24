"""
Skyramp client object which can be used to interact with a k8s cluster.
"""
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

class _K8SClient(_ClientBase):
    """
    Skyramp client object which can be used to interact with a k8s cluster.
    """
    def __init__(
        self,
        kubeconfig_path: Optional[str] = "",
        cluster_name: Optional[str] = "",
        context: Optional[str] = "",
        namespace: Optional[str]=None,
        framework: Optional[str]=None,
        worker_image: Optional[str]="",
        local_image: Optional[bool]=False,
    ) -> None:
        """
        Initializes a Skyramp Client.

        Args:
            kubeconfig_path: The filesystem path of a kubeconfig
            cluster_name: The name of the cluster.
            context: The Kubernetes context within a kubeconfig
        """
        super().__init__()
        self.kubeconfig_path = kubeconfig_path
        self.cluster_name = cluster_name
        self.context = context
        self.framework = framework
        self.worker_image = worker_image
        self.local_image = local_image
        self.project_path = ""
        self.global_headers = {}
        if namespace is not None and namespace != "":
            self.namespace = namespace
        else:
            self.namespace = ""

    def apply_local(self) -> None:
        """
        Creates a local cluster.
        """
        apply_local_function = _library.applyLocalWrapper
        argtypes = []
        restype = ctypes.c_char_p

        _call_function(apply_local_function, argtypes, restype, [])

        self.kubeconfig_path = self._get_kubeconfig_path()
        if not self.kubeconfig_path:
            raise Exception("no kubeconfig found")

    def remove_local(self) -> None:
        """
        Removes a local cluster.
        """
        func = _library.removeLocalWrapper
        argtypes = []
        restype = ctypes.c_char_p

        _call_function(func, argtypes, restype, [])

    def add_kubeconfig(
        self,
        context: str,
        cluster_name: str,
        kubeconfig_path: str,
    ) -> None:
        """
        Adds a preexisting Kubeconfig file to Skyramp.

        Args:
            context: The kubeconfig context to use
            cluster_name: Name of the cluster
            kubeconfig_path: filepath of the kubeconfig
        """
        func = _library.addKubeconfigWrapper
        argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        restype = ctypes.c_char_p

        _call_function(
            func,
            argtypes,
            restype,
            [
                context.encode(),
                cluster_name.encode(),
                kubeconfig_path.encode(),
            ],
        )

        self.kubeconfig_path = kubeconfig_path

    def remove_cluster(self, cluster_name: str) -> None:
        """
        Removes a cluster, corresponding to the name, from Skyramp
        """
        func = _library.removeClusterFromConfigWrapper
        argtypes = [ctypes.c_char_p]
        restype = ctypes.c_char_p

        _call_function(func, argtypes, restype, [cluster_name.encode()])

    def deploy_target(
        self,
        target_description_path: str,
        namespace: str,
        worker_image: str,
        local_image: bool,
    ) -> None:
        super()._deploy_target(target_description_path, namespace, worker_image, local_image,
                             self.kubeconfig_path, self.context, self.cluster_name)

    def delete_target(
        self,
        target_description_path: str,
        namespace: str
    ) -> None:
        super()._delete_target(target_description_path, namespace,
                             self.kubeconfig_path, self.context, self.cluster_name)

    def deploy_skyramp_worker(
        self, namespace: str="", worker_image: str='', local_image: bool=False,
    ) -> None:
        """
        Installs a Skyramp worker onto a cluster if one is registered with Skyramp

        Args:
            namespace: The namespace to deploy the worker to
            worker_image: The image of the worker
            local_image: Whether the image is local(default- False)
        """

        if namespace == "" and self.namespace != "":
            namespace = self.namespace
        namespace = "default" if namespace == "" else namespace

        func = _library.deploySkyrampWorkerWrapper
        argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
                    ctypes.c_char_p, ctypes.c_char_p, ctypes.c_bool]
        restype = ctypes.c_char_p

        _call_function(
            func,
            argtypes,
            restype,
            [namespace.encode(),
             self.kubeconfig_path.encode(),
             self.context.encode(),
             self.cluster_name.encode(),
             worker_image.encode(),
             local_image],
        )

    def delete_skyramp_worker(
        self, namespace: str="",
    ) -> None:
        """
        Removes the Skyramp worker, if a Skyramp worker is installed on a registered Skyramp cluster

        Args:
            namespace: The namespace to delete the worker from.
        """
        if namespace == "" and self.namespace != "":
            namespace = self.namespace
        namespace = "default" if namespace == "" else namespace

        func = _library.deleteSkyrampWorkerWrapper
        argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        restype = ctypes.c_char_p

        _call_function(func, argtypes, restype, [namespace.encode(),
                                                 self.kubeconfig_path.encode(),
                                                 self.context.encode(),
                                                 self.cluster_name.encode()])

    def _get_kubeconfig_path(self) -> str:
        func = _library.getKubeConfigPath
        argtypes = []
        restype = ctypes.c_char_p

        return _call_function(func, argtypes, restype, [], True)

    def set_namespace(self, namespace: str) -> None:
        """
        Set namespace of this Skyramp client

        Args:
            namespace: target namespace
        """
        self.namespace = namespace

    def mocker_apply(self,
        response: Union[_ResponseValue, List[_ResponseValue]] = None,
        mock_object: _MockObject = None,
        traffic_config: _TrafficConfig = None,
        **kwargs,
    ) -> None:
        """
        Applies mock configuration to worker in k8s environment

        Args:
            response: The responses to apply to Mocker
            mock_object: Mock object to apply to Mocker
            traffic_config: Traffic config

        """
        namespace = self.namespace if self.namespace != "" else "default"
        namespace = kwargs.pop("namespace", namespace)

        super().mocker_apply_v1(namespace, "", response, mock_object, traffic_config, **kwargs)

    # pylint: disable=too-many-locals
    def tester_start(
        self,
        test_name: str,
        scenario: Union[_Scenario, List[_Scenario]],
        global_headers: Optional[map] = None,
        blocked: Optional[bool] =False,
        global_vars: Optional[map] = None,
        override_code_path: Optional[str] = None,
        override_dict: Optional[dict] = None,
        endpoint_address: Optional[str] = None,
        pip_requirements: Optional[str] = None,
        skip_verify: Optional[bool] = None,
        blobs: Optional[dict] = None,
        is_formatting_enabled: bool = False,
        loadtest_config: Optional[_LoadTestConfig] = None,
        deploy_worker: Optional[bool] = False,
        override_labels: Optional[map] = None,
        **kwargs,
    ) -> TestStatus:
        namespace = self.namespace if self.namespace != "" else "default"
        namespace = kwargs.pop("namespace", namespace)
        # flag to bring up worker in k8s namespace
        if deploy_worker:
            self.deploy_skyramp_worker(
                namespace=namespace,
                worker_image=kwargs.get("worker_image"),
            )
        return super().tester_start_v1(scenario, global_headers, namespace,
                 "", test_name, blocked,
                 global_vars, self.kubeconfig_path, self.context, self.cluster_name,
                 override_code_path, override_dict, endpoint_address,
                 pip_requirements, skip_verify=skip_verify, blobs=blobs,
                 is_formatting_enabled=is_formatting_enabled,
                 loadtest_config=loadtest_config,
                 override_labels=override_labels,
                 **kwargs)

    def execute_request(self, request: _Request,
        skip_verify: Optional[bool] = None,
        global_vars: Optional[map] = None,
        **kwargs,
    ) -> ResponseLog:
        namespace = self.namespace if self.namespace != "" else "default"
        namespace = kwargs.pop("namespace", namespace)

        return super()._execute_request(request,
                       namespace=namespace,
                       kubeconfig_path=self.kubeconfig_path,
                       kubeconfig_context=self.context,
                       cluster_name=self.cluster_name,
                       skip_verify=skip_verify,
                       global_vars=global_vars,
                       **kwargs)

    def execute_scenario(
        self,
        scenario: _Scenario,
        global_headers: Optional[map] = None,
        blocked: Optional[bool] = False,
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
        namespace = self.namespace if self.namespace != "" else "default"
        namespace = kwargs.pop("namespace", namespace)

        return super()._execute_scenario(scenario.name,
                    scenario,
                    global_headers,
                    namespace,
                    "",
                    blocked,
                    global_vars,
                    self.kubeconfig_path,
                    self.context,
                    self.cluster_name,
                    override_code_path,
                    endpoint_address,
                    pip_requirements,
                    skip_verify=skip_verify, blobs=blobs,
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
        namespace = self.namespace if self.namespace != "" else "default"
        namespace = kwargs.pop("namespace", namespace)

        return super()._get_tester_status(
            namespace,
            self.kubeconfig_path,
            self.context,
            self.cluster_name,
            "",
            tester_id,
            blocked=blocked,
            is_formatting_enabled=is_formatting_enabled,
            **kwargs,
        )
