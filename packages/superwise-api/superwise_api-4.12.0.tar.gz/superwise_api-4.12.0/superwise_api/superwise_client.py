from typing import Optional

import requests

from superwise_api.client.api_client import ApiClient
from superwise_api.client.exceptions import UnauthorizedException
from superwise_api.config import Settings
from superwise_api.entities.agent import AgentApi
from superwise_api.entities.dashboard import DashboardApi
from superwise_api.entities.dashboard_item import DashboardItemApi
from superwise_api.entities.dataset import DatasetApi
from superwise_api.entities.dataset_source import DatasetSourceApi
from superwise_api.entities.destination import DestinationApi
from superwise_api.entities.guardrails import GuardrailsApi
from superwise_api.entities.integration import IntegrationApi
from superwise_api.entities.knowledge import KnowledgeApi
from superwise_api.entities.mcp import McpApi
from superwise_api.entities.model import ModelApi
from superwise_api.entities.policy import PolicyApi
from superwise_api.entities.source import SourceApi
from superwise_api.entities.tag import TagApi


class SuperwiseClient(ApiClient):
    """
    This class provides methods to interact with the Superwise API.

    Attributes:
        settings (Settings): An instance of the Settings class to manage API settings.
        configuration (Configuration): An instance of the Configuration class to manage API configuration.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        auth_host: Optional[str] = None,
        api_host: Optional[str] = None,
        use_hosted_auth: Optional[bool] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        params_without_none_values = {k: v for k, v in locals().items() if v is not None and k != "self"}
        self.settings = Settings(
            **params_without_none_values,
        )
        self.configuration.host = self.settings.api_host
        self.configuration.access_token = self._fetch_token(
            auth_url=self.settings.auth_url,
            client_id=self.settings.client_id,
            client_secret=self.settings.client_secret,
        )
        self._dataset = DatasetApi(self)
        self._model = ModelApi(self)
        self._policy = PolicyApi(self)
        self._destination = DestinationApi(self)
        self._integration = IntegrationApi(self)
        self._source = SourceApi(self)
        self._dataset_source = DatasetSourceApi(self)
        self._dashboard = DashboardApi(self)
        self._dashboard_item = DashboardItemApi(self)
        self._agent = AgentApi(self)
        self._mcp = McpApi(self)
        self._tag = TagApi(self)
        self._knowledge = KnowledgeApi(self)
        self._guardrails = GuardrailsApi(self)

    @property
    def dataset(self):
        return self._dataset

    @property
    def model(self):
        return self._model

    @property
    def policy(self):
        return self._policy

    @property
    def destination(self):
        return self._destination

    @property
    def integration(self):
        return self._integration

    @property
    def source(self):
        return self._source

    @property
    def dataset_source(self):
        return self._dataset_source

    @property
    def dashboard(self):
        return self._dashboard

    @property
    def dashboard_item(self):
        return self._dashboard_item

    @property
    def agent(self):
        return self._agent

    @property
    def knowledge(self):
        return self._knowledge

    @property
    def guardrails(self):
        return self._guardrails

    @property
    def mcp(self):
        return self._mcp

    @property
    def tag(self):
        return self._tag

    @staticmethod
    def _fetch_token(auth_url: str, client_id: str, client_secret: str) -> str:
        """
        Fetches the access token for the API.

        Args:
            auth_url (str): The authentication URL.
            client_id (str): The client ID.
            client_secret (str): The client secret.

        Returns:
            str: The access token.
        """
        response = requests.post(
            auth_url,
            json={
                "clientId": client_id,
                "secret": client_secret,
            },
            headers={"accept": "application/json", "content-type": "application/json"},
        )
        response.raise_for_status()
        return response.json()["accessToken"]

    def call_api(self, *args, **kwargs):
        """
        Calls the API.

        Args:
            *args: Arbitrary positional arguments.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The API response.

        Raises:
            UnauthorizedException: If the API call is unauthorized.
        """
        try:
            return super().call_api(*args, **kwargs)
        except UnauthorizedException:
            self.configuration.access_token = self._fetch_token(
                auth_url=self.settings.auth_url,
                client_id=self.settings.client_id,
                client_secret=self.settings.client_secret,
            )
            return super().call_api(*args, **kwargs)

    def request(self, *args, **kwargs):
        """
        Sends a request to the API.

        Args:
            *args: Arbitrary positional arguments.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The API response. (Handling 204 where no content as an empty dict)
        """
        response = super().request(*args, **kwargs)

        if response.status == 204 and not response.data:
            response.data = b"{}"

        return response
