"""
Contains helpers for interacting with Skyramp user credential
"""
class _UserCredential:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

        self.user_credential = {
            "username": self.username,
            "password": self.password,
        }

    def to_json(self):
        """
        Convert the object to a JSON string.
        """
        return {
            "username": self.username,
            "password": self.password,
        }
