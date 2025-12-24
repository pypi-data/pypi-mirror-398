from typing import Optional

from pydantic import conint

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.dataset_source.dataset_source import DatasetSource
from superwise_api.models.dataset_source.dataset_source import IngestType


class DatasetSourceApi(BaseApi):
    """
    This class provides methods to interact with the DatasetSource API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
    """

    _model_name = "dataset_source"
    _resource_path = "/v1/dataset-sources"
    _model_class = DatasetSource

    def get_by_id(self, dataset_source_id: str, **kwargs) -> DatasetSource:
        """
        Retrieves a connection between Dataset and Source by its id.

        Args:
            dataset_source_id (str): The id of the connection between Dataset and Source to retrieve.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            DatasetSource: The retrieved dataset.
        """
        return super().get_by_id(_id=dataset_source_id, **kwargs)

    def delete(self, dataset_source_id: str, **kwargs):
        """
        Deletes a dataset.

        Args:
            dataset_source_id (str): The id of the connection between dataset and a source to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=dataset_source_id, **kwargs)

    def create(
        self,
        dataset_id: str,
        source_id: str,
        ingest_type: IngestType,
        folder: str,
        **kwargs,
    ) -> DatasetSource:
        """
        Creates a new dataset.

        Args:
            dataset_id (str): The id of the dataset.
            source_id (str): The id of the source.
            ingest_type (IngestType): The ingest type.
            folder (str): The folder.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            DatasetSource: The created dataset.
        """
        data = dict(dataset_id=dataset_id, source_id=source_id, ingest_type=ingest_type, folder=folder)
        return self.api_client.create(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=DatasetSource,
            data=data,
            **kwargs,
        )

    def get(
        self,
        source_id: Optional[str] = None,
        dataset_id: Optional[str] = None,
        folder: Optional[str] = None,
        ingest_type: Optional[IngestType] = None,
        id: Optional[str] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=1)] = None,
        **kwargs,
    ) -> Page:
        """
        Retrieves datasets based on the provided filters.

        Args:
            source_id (Optional[str], optional): The id of the source to retrieve by.
            dataset_id (Optional[str], optional): The id of the dataset to retrieve by.
            folder (Optional[str], optional): The folder of the dataset to retrieve by.
            ingest_type (Optional[IngestType], optional): The ingest type of the dataset to retrieve by.
            id (Optional[str], optional): The id of the dataset to retrieve by.
            page (Optional[conint(strict=True, ge=1)], optional): The page number to retrieve.
            size (Optional[conint(strict=True, le=500, ge=1)], optional): The number of datasets to retrieve per page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of datasets.
        """
        query_params = {
            k: v
            for k, v in dict(
                source_id=source_id,
                dataset_id=dataset_id,
                folder=folder,
                ingest_type=ingest_type,
                id=id,
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=DatasetSource,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        dataset_source_id: str,
        *,
        folder: Optional[str] = None,
        ingest_type: Optional[IngestType] = None,
        **kwargs,
    ) -> DatasetSource:
        """
        Updates a dataset.

        Args:
            dataset_source_id (str): The id of the connection between dataset and a source to update.
            folder (Optional[str], optional): The folder to update.
            ingest_type (Optional[IngestType], optional): The ingest type to update.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            DatasetSource: The updated connection between a dataset and a source.
        """
        if not any([folder, ingest_type]):
            raise ValueError("At least one of the following parameters must be provided: folder, ingest_type")

        data = {k: v for k, v in dict(folder=folder, ingest_type=ingest_type).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            entity_id=dataset_source_id,
            model_name=self._model_name,
            model_class=DatasetSource,
            data=data,
            **kwargs,
        )
