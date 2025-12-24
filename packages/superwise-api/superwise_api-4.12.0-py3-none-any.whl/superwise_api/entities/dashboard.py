from typing import Dict, Literal, Any
from typing import Optional

from pydantic import conint

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.dashboard.dashboard import Dashboard
from superwise_api.models.dashboard.dashboard import WidgetMeta
from superwise_api.models.utils import SearchParams


class DashboardApi(BaseApi):
    """
    This class provides methods to interact with the Dashboard API.

    Args:
        api_client (SuperwiseClient): An instance of the ApiClient to make requests.
    """

    _model_name = "dashboard"
    _resource_path = "/v1/dashboards"
    _model_class = Dashboard

    def create(self, name: str, **kwargs) -> Dashboard:
        """
        Creates a new dashboard.

        Args:
            name (str): The name of the dashboard.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dashboard: The created dashboard.
        """
        data = {
            "name": name,
        }
        return self.api_client.create(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            data=data,
            **kwargs,
        )

    def get(
        self,
        name: Optional[str] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=1)] = None,
        **kwargs,
    ) -> Page:
        """
        Gets all dashboards.

        Args:
            name (str, optional): The name of the dashboard.
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of sources.
        """
        query_params = {k: v for k, v in dict(name=name, page=page, size=size).items() if v is not None}
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        dashboard_id: str,
        *,
        name: Optional[str] = None,
        positions: Optional[Dict[str, WidgetMeta]] = None,
        **kwargs,
    ):
        """
        Updates a dashboard.

        Args:
            dashboard_id (str): The id of the dashboard.
            name (str, optional): The new name of the dashboard.
            positions (dict, optional): The new positions of the widgets.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Dashboard: The updated dashboard.
        """
        if not any([name, positions]):
            raise ValueError("At least one parameter must be provided to update the dashboard.")

        data = {k: v for k, v in dict(name=name, positions=positions).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            entity_id=dashboard_id,
            model_name=self._model_name,
            model_class=self._model_class,
            data=data,
            **kwargs,
        )

    def add_tags(
        self,
        dashboard_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Add tags to an dashboard.

        Args:
            dashboard_id (str): The id of the dashboard.
            tag_ids list(str): List of tag ids to add the dashboard
        Returns:
            None
        """
        return self.api_client.post(
            resource_path=self._resource_path + f"/{dashboard_id}/tags",
            data=tag_ids,
            **kwargs,
        )

    def remove_tags(
        self,
        dashboard_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Delete tags from an dashboard.

        Args:
            dashboard_id (str): The id of the dashboard.
            tag_ids list(str): List of tag ids to remove from the dashboard
        Returns:
            None
        """
        return self.api_client.delete(
            resource_path=self._resource_path + "/{dashboard_id}/tags",
            model_name=self._model_name,
            entity_id=dashboard_id,
            path_params={"dashboard_id": dashboard_id},
            query_params=[("ids", id) for id in tag_ids],
            **kwargs,
        )

    def search(
        self,
        filters: list[Any] | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_direction: Literal["asc", "desc"] = "desc",
        **kwargs,
    ) -> Page:
        """
        Searches for dashboards based on a prefix.

        Args:
            filters (list[Any]): Filter on db columns, list of tuples.
                e.g. [[["id", "eq", "5c05dc9f-f04a-4ce8-9d57-2ec63ee76aac"], "and", ["description", "ilike", "Construction"]], "or", ["name", "ilike", "active"]]
            search (str): Free text search on searchable fields
            sort_by (str): Field to sort by
            sort_direction (Literal["asc", "desc"]): Sort direction (ascending or descending)
            query_params can be passed as part of the kwargs for pagination

        Returns:
            Page: A page of dashboards.
        """
        data = SearchParams(
            filters=filters,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
        ).model_dump(exclude_none=True)
        response_types_map = {
            "200": Page.set_model(self._model_class),
            "422": None,
            "500": None,
        }
        return self.api_client.post(
            resource_path=f"{self._resource_path}/search",
            data=data,
            response_types_map=response_types_map,
            **kwargs,
        )
