from pydantic import BaseModel

from superwise_api.entities.base import BaseApi
from superwise_api.models.tag.tag import Tag


class TagApi(BaseApi):
    """
    This class provides methods to interact with the tag API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
        _model_class (TagApi): The model class.
    """

    _model_name = "tag"
    _resource_path = "/v1/tags"
    _model_class = Tag

    def get_by_id(self, tag_id: str, **kwargs) -> dict:
        """
        Gets tag by id.

        Args:
            tag_id (str): The id of the tag.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            TAG: The TAG entity.
        """
        return super().get_by_id(_id=tag_id, **kwargs)

    def delete(self, tag_id: str, **kwargs) -> None:
        """
        Deletes tag.

        Args:
            tag_id (str): The id of the tag to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=tag_id, **kwargs)

    def create(self, name: str, color: str, **kwargs) -> Tag:
        """
        Creates new tag.

        Args:
            name (str): The name of the tag entity.
            color (str): The color of the tag.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Tag: The created tag entity.
        """

        data = {"name": name, "color": color}
        return self.api_client.create(
            resource_path=self._resource_path, model_class=Tag, model_name=self._model_name, data=data, **kwargs
        )

    def get(
        self,
        **kwargs,
    ) -> list[Tag]:
        """
        Retrieves tag. Filter if any of the parameters are provided.

        Args:
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of tag.
        """
        return self.api_client.get(
            resource_path=self._resource_path,
            model_class=Tag,
            model_name=self._model_name,
            query_params=None,
            paginate=False,
            **kwargs,
        )

    def update(self, tag_id: str, name: str | None = None, color: str | None = None, **kwargs) -> BaseModel:
        """
        Updates tag.

        Args:
            tag_id (str): The id of the tag.
            name (str, optional): The new name of the tag.
            color (str, optional): The new color of the tag.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Tag: The updated tag.
        """
        data = {"name": name, "color": color}
        data = {k: v for k, v in data.items() if v is not None}
        if len(data) == 0:
            raise ValueError("At least one parameter must be provided to update the agent.")
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Tag,
            entity_id=tag_id,
            data=data,
            **kwargs,
        )
