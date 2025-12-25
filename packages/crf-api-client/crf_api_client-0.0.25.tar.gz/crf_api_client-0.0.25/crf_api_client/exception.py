import requests


class CRFAPIError(Exception):
    def __init__(self, message: str, response: requests.Response):
        self.message = message
        self.response = response
        super().__init__(self.message)
