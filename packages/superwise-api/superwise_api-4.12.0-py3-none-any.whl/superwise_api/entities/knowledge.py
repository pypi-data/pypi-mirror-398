from os import PathLike
from typing import Optional

from pydantic import BaseModel

from superwise_api.client.exceptions import ApiTypeError
from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.knowledge.knowledge import Knowledge
from superwise_api.models.tool.tool import EmbeddingModel
from superwise_api.models.tool.tool import FileInfo
from superwise_api.models.tool.tool import KnowledgeMetadata
from superwise_api.models.tool.tool import UploadResponse


class KnowledgeApi(BaseApi):
    """
    This class provides methods to interact with the KnowledgeApi API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _model_class (KnowledgeApi): The model class.
    """

    _model_name = "knowledgeApi"
    _resource_path = "/v1/knowledge"
    _model_class = Knowledge

    def get_by_id(self, knowledge_id: str, **kwargs) -> dict:
        """
        Gets knowledge by id.

        Args:
            knowledge_id (str): The id of the knowledge.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Knowledge: The knowledge.
        """
        return super().get_by_id(_id=knowledge_id, **kwargs)

    def delete(self, knowledge_id: str, **kwargs) -> None:
        """
        Deletes knowledge.

        Args:
            knowledge_id (str): The id of the knowledge.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=knowledge_id, **kwargs)

    def create(
        self, name: str, knowledge_metadata: KnowledgeMetadata, embedding_model: EmbeddingModel, **kwargs
    ) -> BaseModel:
        """
        Creates new knowledge.

        Args:
            name (str): The name of the knowledge.
            knowledge_metadata (superwise_api.models.tool.tool.KnowledgeMetadata): knowledge params.
            embedding_model (EmbeddingModel): The parameters of the embedding model.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Knowledge: The created knowledge.
        """
        if knowledge_metadata.type == "file":
            upload_response = self._upload(kwargs.pop("files", {}))
            if any([response.status != "success" for response in upload_response.files]):
                return upload_response
            knowledge_metadata.file_ids = [str(response.file_info.id) for response in upload_response.files]

        data = dict(
            name=name, knowledge_metadata=knowledge_metadata.model_dump(), embedding_model=embedding_model.model_dump()
        )
        return self.api_client.create(
            resource_path=self._resource_path, model_class=Knowledge, model_name=self._model_name, data=data, **kwargs
        )

    def _upload(self, files: dict[str, PathLike], **kwargs) -> UploadResponse:
        """
        Upload Knowledge files to cloud storage.

        Args:
            files: list of paths for the files to upload.

        Returns:
            Upload response: upload status of each file
        """
        response_types_map = {
            "202": UploadResponse,
            "422": "HTTPValidationError",
        }

        return self.api_client.post(
            resource_path=self._resource_path + "/upload",
            model_name=self._model_name,
            response_types_map=response_types_map,
            files=files,
            _content_type="multipart/form-data",
            **kwargs,
        )

    def get(self, page: Optional[int] = None, size: Optional[int] = None, **kwargs) -> Page:
        """
        Retrieves knowledge. Filter if any of the parameters are provided.

        Args:
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of knowledge.
        """
        query_params = {
            k: v
            for k, v in dict(
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_class=Knowledge,
            model_name=self._model_name,
            query_params=query_params,
            **kwargs,
        )

    def update(self, knowledge_id: str, name: Optional[str] = None, **kwargs) -> BaseModel:
        """
        Updates knowledge.

        Args:
            knowledge_id (str): The id of the knowledge.
            name (str, optional): The new name of the knowledge.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Knowledge: The updated knowledge.
        """
        if not any([name]):
            raise ValueError("At least one parameter must be provided to update the knowledge.")

        data = {k: v for k, v in dict(name=name).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Knowledge,
            entity_id=knowledge_id,
            data=data,
            **kwargs,
        )

    def get_files_info(self, file_ids: list[str], **kwargs) -> list[FileInfo]:
        """
        Retrieves file info.

        Args:
            file_ids: list of file ids to receive info about.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list[FileInfo]: A list of FileInfo for each requested id.
        """
        resource_path = self._resource_path + "/file_info/{file_ids}"
        _params = locals()

        _all_params = [
            "async_req",
            "_request_auth",
            "_content_type",
            "_headers",
        ]
        for _key, _val in _params["kwargs"].items():
            if _key not in _all_params:
                raise ApiTypeError(f"Got an unexpected keyword argument '{_key}' to method get_files_info")
            _params[_key] = _val
        del _params["kwargs"]

        _collection_formats = {}

        _path_params = {"file_ids": "_".join(file_ids)}

        # process the header parameters
        _header_params = dict(_params.get("_headers", {}))
        # set the HTTP header `Accept`
        _header_params["Accept"] = "application/json"

        _response_types_map = {
            "200": FileInfo,
            "404": None,
            "422": None,
            "500": None,
        }

        return self.api_client.call_api(
            resource_path,
            "GET",
            query_params={},
            path_params=_path_params,
            header_params=_header_params,
            response_types_map=_response_types_map,
            auth_settings=["implicit"],
            async_req=_params.get("async_req"),
            _return_http_data_only=_params.get("_return_http_data_only"),
            _preload_content=_params.get("_preload_content", True),
            _request_timeout=_params.get("_request_timeout"),
            _request_auth=_params.get("_request_auth"),
        )

    def reindex_url_knowledge(self, knowledge_id: str, **kwargs) -> Knowledge:
        """
        Reindex url knowledge.

        Args:
            knowledge_id: id of the knowledge to reindex.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Knowledge: the reindexed knowledge
        """
        response_types_map = {
            "200": Knowledge,
            "404": None,
            "422": None,
            "500": None,
        }
        return self.api_client.post(
            resource_path=self._resource_path + f"/{knowledge_id}/reindex",
            model_name=self._model_name,
            response_types_map=response_types_map,
            **kwargs,
        )
