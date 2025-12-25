import logging

import requests

logger = logging.getLogger(__name__)


class SAGeodataAPI:
    """Class for using the test version of the SA Geodata API.
    Used for the wellcompletionreports endpoint testing etc.

    Args:
        env (str): either "qa" or "dev" - production is unavailable.

    """

    def __init__(self, env="qa"):
        self.env = env

    def authenticate(self):
        """Authenticate this session using username and password
        "Admin" (this is for dev and test only)"""
        response = requests.post(
            f"https://api.{self.env}.sageo.env.sa.gov.au/api/v1.0/token",
            json={
                "username": "Admin",
                "password": "Admin",
            },
            verify=False,
        )
        self.token = response.json()["token"]

    def get(self, endpoint, prefix="api/v1.0", query="", **kwargs):
        """Send GET request.

        Args:
            endpoint (str): used in https://api.ENV.sageo.env.sa.gov.au/PREFIX/ENDPOINT
            prefix (str): by default "api/v1.0"
            query (str): appended after ENDPOINT/

        ENV is self.env

        PREFIX is "api/v1.0" by default

        This method adds the relevant authentication headers.

        """
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"bearer {self.token}"
        kwargs["headers"] = headers
        kwargs["verify"] = kwargs.get("verify", False)
        url = (
            f"https://api.{self.env}.sageo.env.sa.gov.au/{prefix}/{endpoint}/"
            + f"{query}"
        )
        logger.debug(f"Get: {url}")
        response = requests.get(url, **kwargs)
        return response

    def post(self, endpoint, prefix="api/v1.0", query="", **kwargs):
        """Send GET request.

        Args:
            endpoint (str): used in https://api.ENV.sageo.env.sa.gov.au/PREFIX/ENDPOINT
            prefix (str): by default "api/v1.0"
            query (str): appended after ENDPOINT/

        ENV is self.env

        PREFIX is "api/v1.0" by default

        This method adds the relevant authentication headers.

        """
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"bearer {self.token}"
        kwargs["headers"] = headers
        kwargs["verify"] = kwargs.get("verify", False)
        url = (
            f"https://api.{self.env}.sageo.env.sa.gov.au/{prefix}/{endpoint}/"
            + f"{query}"
        )
        logger.debug(f"URL: {url}")
        response = requests.post(url, **kwargs)
        return response

    @staticmethod
    def convert_message(msg):
        """When the API returns an error message it encodes the error's JSON, making
        it hard to read. This unpacks that. Accepts and returns a string."""
        msg = msg.strip("[").strip("]")
        errors = msg.split("},{")
        errors_proper = []
        for error in errors[:]:
            code, descr = error.split(",Description:")
            code = code.split(":")[1]
            descr = descr.strip("{").strip("}")
            errors_proper.append({"ErrorCode": code, "Description": descr})
        return errors_proper
