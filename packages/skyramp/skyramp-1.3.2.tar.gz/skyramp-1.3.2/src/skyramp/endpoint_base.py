"""
Containes endpoint base definition
"""

from abc import ABC

class _EndpointBase(ABC):
    """
    This is class is to prevent cyclic imports 
    until classes dependencies are cleaned up
    """

    def __init__(self):
        pass

    def get_method_name_for_method_type(self, method_type):
        """
        returns method_name of given method_type
        """

    def get_endpoint(self):
        """ 
        returns dict of underlying endpoint object
        """
