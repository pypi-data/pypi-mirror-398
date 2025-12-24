from typing import Optional

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.destination.destination import Destination, SlackDestinationParams


class DestinationApi(BaseApi):
    """
    This class provides methods to interact with the Destination API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _model_class (Destination): The model class.
    """

    _model_name = "destination"
    _resource_path = "/v1/destinations"
    _model_class = Destination

    def get_by_id(self, destination_id: str, **kwargs) -> dict:
        """
        Gets a destination by id.

        Args:
            destination_id (str): The id of the destination.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Destination: The destination.
        """
        return super().get_by_id(_id=destination_id, **kwargs)

    def delete(self, destination_id: str, **kwargs) -> None:
        """
        Deletes a destination.

        Args:
            destination_id (str): The id of the destination.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=destination_id, **kwargs)

    def create(self, name: str, integration_id: str, params: SlackDestinationParams, **kwargs) -> dict:
        """
        Creates a new destination.

        Args:
            name (str): The name of the destination.
            integration_id (str): The id of the integration.
            params (dict): The parameters of the destination.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Destination: The created destination.
        """
        data = {k: v for k, v in dict(name=name, integration_id=integration_id, params=params).items() if v is not None}
        return self.api_client.create(
            resource_path=self._resource_path, model_class=Destination, model_name=self._model_name, data=data, **kwargs
        )

    def get(
        self,
        name: Optional[str] = None,
        integration_id: Optional[str] = None,
        destination_id: Optional[str] = None,
        created_by: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> Page:
        """
        Retrieves destinations. Filter if any of the parameters are provided.

        Args:
            name (str, optional): The name of the destination.
            integration_id (str, optional): The id of the integration.
            destination_id (str, optional): The id of the destination.
            created_by (str, optional): The creator of the destination.
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of destinations.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name,
                integration_id=integration_id,
                destination_id=destination_id,
                created_by=created_by,
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_class=Destination,
            model_name=self._model_name,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        destination_id: str,
        *,
        name: Optional[str] = None,
        params: Optional[SlackDestinationParams] = None,
        **kwargs,
    ) -> dict:
        """
        Updates a destination.

        Args:
            destination_id (str): The id of the destination.
            name (str, optional): The new name of the destination.
            params (dict, optional): The new parameters of the destination.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Destination: The updated destination.
        """
        if not any([name, params]):
            raise ValueError("At least one parameter must be provided to update the destination.")

        data = {k: v for k, v in dict(name=name, params=params).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Destination,
            entity_id=destination_id,
            data=data,
            **kwargs,
        )
