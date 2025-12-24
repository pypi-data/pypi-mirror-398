"""
Contains helpers for interacting with Skyramp rest param.
"""
class _RestParam:
    def __init__(self, name: str, in_: str, value=None, type_=None, filepath=None, decoded=None):
        self.name = name
        self.in_ = in_
        self.type_ = type_
        self.value = value
        self.filepath = filepath
        self.decoded = decoded

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        ret = {
            "name": self.name,
            "in": self.in_,
        }

        if self.value is not None:
            ret["value"] = self.value
        if self.filepath is not None and self.filepath != "":
            ret["filepath"] = self.filepath
        if self.decoded is not None and self.decoded is True:
            ret["decoded"] = self.decoded

        return ret


class _PathParam(_RestParam):
    def __init__(self, name: str, value=None):
        super().__init__(name, "path", value)


class _QueryParam(_RestParam):
    def __init__(self, name: str, value=None):
        super().__init__(name, "query", value)


class _FormParam(_RestParam):
    def __init__(self, name: str, value=None):
        super().__init__(name, "form", value)


class _MultipartParam(_RestParam):
    def __init__(self, name: str, value=None, filename="", decoded=False):
        super().__init__(name, "multipart", value, filepath=filename, decoded=decoded)
