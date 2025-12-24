"""
Defines a Skyramp client, which can be used to interact with a cluster.
"""

import ctypes
import json
import os
from typing import Optional, Any, Union

from skyramp.utils import _library, check_for_update
from skyramp.test_response2 import ResponseV2
from skyramp.docker_client import _DockerClient
from skyramp.k8s_client import _K8SClient
from skyramp.local_client import _LocalClient

class ReturnType(ctypes.Structure):
    """c type for return value from core"""

    _fields_ = [
        ("response", ctypes.c_char_p),
        ("error", ctypes.c_char_p),
    ]


def _client(k8s_config_path: Optional[str]="",
            k8s_context: Optional[str]="",
            cluster_name: Optional[str]="",
            k8s_namespace: Optional[str]="",
            worker_address: Optional[str]="",
            docker_network: Optional[str]="",
            docker_skyramp_port: Optional[int]=None,
            framework: Optional[str]="",
            runtime: Optional[str]="",
            worker_image: Optional[str]="",
            local_image: Optional[bool]=False,
            ):
    """
    Create Skyramp Client
    if worker_address is provided, it creates a docker client
    if one of k8s_config_path, k8s_context, cluster_name, and/or k8s_namespace is given,
    it creates a k8s client
    """
    check_for_update("python")

    if runtime == "docker" and docker_skyramp_port is not None:
        skyramp_in_docker = os.getenv('SKYRAMP_IN_DOCKER')
        hostname = "localhost"
        if skyramp_in_docker:
            hostname = "host.docker.internal"
        worker_address = f"{hostname}:{docker_skyramp_port}"

    if worker_address != "" and (k8s_namespace != "" or
             k8s_config_path != "" or k8s_context != "" or cluster_name != ""):
        raise Exception("Address cannot be used with k8s related parameters")

    if worker_address == "" and k8s_namespace == "" and \
            k8s_config_path  == "" and k8s_context == "" and cluster_name == "":
        return _LocalClient(framework=framework)

    if worker_address != "":
        return _DockerClient(worker_address, network_name=docker_network, framework=framework,
                                worker_image=worker_image, local_image=local_image)

    return _K8SClient(k8s_config_path, cluster_name, k8s_context, k8s_namespace,
                      framework=framework, worker_image=worker_image, local_image=local_image)

def check_status_code(response: ResponseV2, expected_status: str) -> bool:
    """
    Checks if the response's status code matches the expected status code 
    (with support for wildcards).
    """
    try:
        func = _library.checkStatusCodeWrapper
        func.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
        ]
        func.restype = ctypes.c_int
        args = [
            response.status_code,
            expected_status.encode(),
        ]
        result = func(*args)
        if int(result) == 0:
            return False
        if int(result) == 1:
            return True

        raise Exception('No response from wrapper')

    except Exception as err:
        print(f"Error in checkStatusCode: {str(err)}")
        raise  # Re-throw to allow caller to handle errors

def get_response_value(response: ResponseV2, json_path: str) -> Optional[Any]:
    """
    get value from response body using json_path
    """
    if response.response_body is None:
        return None
    func = _library.getJSONValueWrapper
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    func.restype = ctypes.c_char_p
    args = [
        response.response_body.encode(),
        json_path.encode(),
    ]
    result = func(*args)

    if result is None:
        return None

    try:
        # Decode the bytes to string
        json_str = result.decode('utf-8')
        # Parse the JSON string
        parsed = json.loads(json_str)

        # Handle different types
        if isinstance(parsed, dict) and "type" in parsed and "value" in parsed:
            value_type = parsed["type"]
            value = parsed["value"]

            # Return None for complex types (arrays and objects)
            if value_type in ["array", "object" , "[]interface {}"]:
                return None

            ret = value
            # Cast to appropriate Python type
            if value_type == "string":
                ret =  str(value)
            elif value_type == "number":
                ret = float(value) if '.' in str(value) else int(value)
            elif value_type == "boolean":
                ret = bool(value)
            elif value_type == "null":
                ret = None
            return ret
        return parsed
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as exception:
        print(f"Error processing JSONValue: {exception}")
        return None

def check_schema(response: "ResponseV2", expected_schema: [dict, str]) -> bool:
    """
    Validates the response body against the expected schema.

    :param response: The response object containing the JSON body.
    :param expected_schema: The JSON schema to validate against.
    :return: True if the schema matches, False otherwise.
    """
    func = _library.checkSchemaWrapper
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    func.restype = ctypes.c_char_p
    args = [
        response.response_body.encode(),
        expected_schema.encode(),
    ]
    result = func(*args)

    if result is None:
        return False

    try:
        # Decode the bytes to string
        json_str = result.decode('utf-8')
        # Parse the JSON string
        parsed = json.loads(json_str)
        return parsed['result']
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
        # return false for other errors
        return False


def iterate(blob: str) -> list[str]:
    """
    Generates a list of json paths from a given blob

    :param blob: blob to traverse
    """
    arg = blob
    if isinstance(blob, dict):
        arg = json.dumps(blob)

    func = _library.generateJsonTreePathsFromBlob
    func.argtypes = [
        ctypes.c_char_p,
    ]
    func.restype = ctypes.c_char_p
    args = [
        arg.encode(),
    ]
    result = func(*args)
    if result is None:
        return []

    try:
        json_str = result.decode('utf-8')
        parsed = json.loads(json_str)
        return parsed
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
        return []


def get_value(blob: Union[str, dict], json_path: str) -> Optional[any]:
    """
    get value from blob using json_path
    """
    func = _library.getJSONValueWrapper
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    func.restype = ctypes.c_char_p

    arg = blob
    if isinstance(blob, dict):
        arg = json.dumps(blob)

    args = [
        arg.encode(),
        json_path.encode(),
    ]
    result = func(*args)

    if result is None:
        return None

    try:
        # Decode the bytes to string
        json_str = result.decode('utf-8')
        # Parse the JSON string
        parsed = json.loads(json_str)

        return parsed["value"]
    except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as exception:
        print(f"Error processing JSONValue: {exception}")
        return None

def get_response_html_input(response: ResponseV2, node: str) -> str:
    """
    get value of html input element
    """
    if response.response_body is None:
        return None

    func = _library.getHtmlInputValueWrapper
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    func.restype = ReturnType
    args = [
        response.response_body.encode(),
        node.encode()
    ]
    result = func(*args)

    if result is not None and result.error:
        raise Exception(ctypes.c_char_p(result.error).value)

    return result.response.decode()

def get_response_value_with_key(response: ResponseV2, key: str) -> str:
    """
    get value from the body with a key
    """
    if response.response_body is None:
        return None

    func = _library.getResponseValueWithKeyWrapper
    func.argtypes = [
        ctypes.c_char_p,
        ctypes.c_char_p,
    ]
    func.restype = ctypes.c_char_p
    args = [
        response.response_body.encode(),
        key.encode()
    ]
    result = func(*args)

    if result is None:
        raise Exception("value not found in response body")

    return result.decode()
