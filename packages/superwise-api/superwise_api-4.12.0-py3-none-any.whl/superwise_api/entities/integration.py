from typing import Optional

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.integration.integration import Integration
from superwise_api.models.integration.integration import IntegrationType


class IntegrationApi(BaseApi):
    """
    This class provides methods to interact with the Integration API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _model_class (Integration): The model class.
    """

    _model_name = "integration"
    _resource_path = "/v1/integrations"
    _model_class = Integration

    def get_by_id(self, integration_id: str, **kwargs) -> Integration:
        """
        Gets an integration by id.

        Args:
            integration_id (str): The id of the integration.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Integration: The integration.
        """
        return super().get_by_id(_id=integration_id, **kwargs)

    def delete(self, integration_id: str, delete_destinations: bool = False, **kwargs):
        """
        Deletes an integration.

        Args:
            integration_id (str): The id of the integration.
            delete_destinations (bool): Whether to delete the destinations associated with the integration.
            **kwargs: Arbitrary keyword arguments.
        """
        return self.api_client.delete(
            resource_path=self._resource_path,
            model_name=self._model_name,
            entity_id=integration_id,
            query_params={"delete_destinations": delete_destinations},
            **kwargs,
        )

    def get(
        self,
        name: Optional[str] = None,
        integration_type: Optional[IntegrationType] = None,
        created_by: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
    ) -> Page:
        """
        Gets all integrations.

        Args:
            name (str, optional): The name of the integration.
            integration_type (IntegrationType, optional): The type of the integration.
            created_by (str, optional): The user who created the integration.
            page (int, optional): The page number.
            size (int, optional): The size of the page.

        Returns:
            Page: A page of integrations.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name, integration_type=integration_type, created_by=created_by, page=page, size=size
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_class=Integration,
            model_name=self._model_name,
            query_params=query_params,
        )
