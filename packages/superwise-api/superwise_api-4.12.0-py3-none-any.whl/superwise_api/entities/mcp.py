from pydantic import BaseModel

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.mcp.mcp import MCP


class McpApi(BaseApi):
    """
    This class provides methods to interact with the Mcp API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _model_class (McpApi): The model class.
    """

    _model_name = "mcp"
    _resource_path = "/v1/mcps"
    _model_class = MCP

    def get_by_id(self, mcp_id: str, **kwargs) -> dict:
        """
        Gets mcp by id.

        Args:
            mcp_id (str): The id of the mcp.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            MCP: The MCP entity.
        """
        return super().get_by_id(_id=mcp_id, **kwargs)

    def delete(self, mcp_id: str, **kwargs) -> None:
        """
        Deletes mcp.

        Args:
            mcp_id (str): The id of the mcp to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=mcp_id, **kwargs)

    def create(self, name: str, url: str, headers: str | None = None, params: str | None = None, **kwargs) -> MCP:
        """
        Creates new mcp.

        Args:
            name (str): The name of the mcp entity.
            url (str): The url of the mcp server.
            headers (str): Authentication headers.
            params (str): optional query parameters for the server requests.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            MCP: The created mcp entity.
        """

        data = {"name": name, "url": url, "headers": headers, "params": params}
        return self.api_client.create(
            resource_path=self._resource_path, model_class=MCP, model_name=self._model_name, data=data, **kwargs
        )

    def get(
        self,
        page: int | None = None,
        size: int | None = None,
        search: str | None = None,
        name: str | None = None,
        url: str | None = None,
        include_disabled: bool | None = None,
        **kwargs,
    ) -> Page:
        """
        Retrieves mcp. Filter if any of the parameters are provided.

        Args:
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of mcp.
        """
        query_params = {
            k: v
            for k, v in dict(
                page=page,
                size=size,
                search=search,
                name=name,
                url=url,
                include_disabled=include_disabled,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_class=MCP,
            model_name=self._model_name,
            query_params=query_params,
            **kwargs,
        )

    def update(self, mcp_id: str, name: str, **kwargs) -> BaseModel:
        """
        Updates mcp.

        Args:
            mcp_id (str): The id of the mcp.
            name (str, optional): The new name of the mcp.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            MCP: The updated mcp.
        """
        data = {"name": name}
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=MCP,
            entity_id=mcp_id,
            data=data,
            **kwargs,
        )
