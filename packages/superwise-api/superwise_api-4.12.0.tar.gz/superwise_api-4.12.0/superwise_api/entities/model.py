from typing import Optional

from pydantic import conint

from superwise_api.entities.base import BaseApi
from superwise_api.models.dataset.dataset import Dataset
from superwise_api.models.model.model import Model, ModelExtended


class ModelApi(BaseApi):
    """
    This class provides methods to interact with the Model API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _dataset_source_model_name (str): The name of the dataset source model.
        _dataset_model_path (str): The path of the dataset source resource.
    """

    _model_name = "model"
    _dataset_source_model_name = "dataset_source"
    _resource_path = "/v1/models"
    _dataset_model_path = "/v1/dataset-models"
    _model_class = Model
    _model_extended_class = ModelExtended

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> Model:
        """
        Creates a new model.

        Args:
            name (str): The name of the model.
            description (str, optional): The description of the model.
            id (str, optional): The id of the dataset.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Model: The created model.
        """
        data = {
            k: v
            for k, v in dict(
                name=name,
                description=description,
                id=id,
            ).items()
            if v is not None
        }
        return self.api_client.create(
            resource_path=self._resource_path, model_name=self._model_name, model_class=Model, data=data, **kwargs
        )

    @BaseApi.raise_exception
    def get(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=1)] = None,
        **kwargs,
    ):
        """
        Retrieves a model by its id.

        Args:
            id (str): The id of the model to retrieve.
            name (str): The name of the model to retrieve.
            created_by (str): The creator of the model to retrieve.
            page (Optional[conint(strict=True, ge=1)], optional): The page number to retrieve.
            size (Optional[conint(strict=True, le=500, ge=1)], optional): The number of datasets to retrieve per page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of models.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name,
                id=id,
                created_by=created_by,
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Model,
            query_params=query_params,
            **kwargs,
        )

    def get_by_id(self, model_id: str, **kwargs) -> Model:
        """
        Retrieves a model by its id.

        Args:
            model_id (str): The id of the model to retrieve.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Model: The retrieved model.
        """
        return super().get_by_id(_id=model_id, **kwargs)

    def update(
        self,
        model_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        id: Optional[str] = None,
        **kwargs,
    ) -> Model:
        """
        Updates a model.

        Args:
            model_id (str): The id of the dataset to model.
            name (str, optional): The new name of the model.
            description (str, optional): The new description of the model.
            id (str, optional): The new id of the model.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Model: The updated model.
        """
        if not any([name, description, id]):
            raise ValueError("At least one parameter must be provided to update the dataset.")

        data = {k: v for k, v in dict(name=name, description=description, id=id).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            entity_id=model_id,
            model_name=self._model_name,
            model_class=Model,
            data=data,
            **kwargs,
        )

    def delete(self, model_id: str, **kwargs):
        """
        Deletes a model.

        Args:
            model_id (str): The id of the model to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=model_id, **kwargs)

    @BaseApi.raise_exception
    def get_datasets_for_model(self, model_id: str, **kwargs):
        """
        Retrieves all datasets for a model.

        Args:
            model_id (str): The id of the model.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of datasets.
        """
        return self.api_client.get(
            resource_path=f"{self._resource_path}/{model_id}/datasets",
            model_name="dataset",
            model_class=Dataset,
            query_params={},
            **kwargs,
        )

    @BaseApi.raise_exception
    def connect_dataset_to_model(self, dataset_id: str, model_id: str, **kwargs):
        """
        Connects a dataset to a model.

        Args:
            dataset_id (str): The id of the dataset.
            model_id (str): The id of the model.
            **kwargs: Arbitrary keyword arguments.
        """
        return self.api_client.post(resource_path=f"{self._dataset_model_path}/{dataset_id}/{model_id}", **kwargs)

    @BaseApi.raise_exception
    def disconnect_dataset_from_model(self, dataset_id: str, model_id: str, **kwargs):
        """
        Disconnects a dataset from a model.

        Args:
            dataset_id (str): The id of the dataset.
            model_id (str): The id of the model.
            **kwargs: Arbitrary keyword arguments.
        """
        return self.api_client.delete(
            resource_path=f"{self._dataset_model_path}/{dataset_id}", model_name="dataset", entity_id=model_id, **kwargs
        )
