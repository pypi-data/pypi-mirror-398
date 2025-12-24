from typing import Literal, Optional, Any
from uuid import UUID

from pydantic import conint
from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.guardrails.guardrails import (
    Guardrail,
    GuardRules,
    GuardrailValidationResponse,
    GuardrailValidationResponses,
    GuardrailVersion,
)
from superwise_api.models.utils import SearchParams


class GuardrailsApi(BaseApi):
    _model_name = "guardrails"
    _model_version_name = "guardrail_version"
    _resource_path = "/v1/guardrails"
    _model_class = Guardrail
    _model_version_class = GuardrailVersion

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs,
    ) -> Guardrail:
        """
        Create a new guardrail.

        Args:
            name: The name of the guardrail.
            description: The description of the guardrail.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The created guardrail.
        """
        response_types_map = {
            "201": self._model_class,
            "401": "HTTPUnauthorized",
            "422": "HTTPValidationError",
        }
        payload = {
            "name": name,
            "description": description,
        }
        return self.api_client.post(
            resource_path=self._resource_path,
            model_name=self._model_name,
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def get_by_id(
        self,
        guardrail_id: str,
        with_deleted: bool = False,
        **kwargs,
    ) -> Guardrail:
        """
        Get a guardrail by id.

        Args:
            guardrail_id: The id of the guardrail.
            with_deleted: Whether to include deleted guardrails.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The guardrail.
        """
        query_params = {"with_deleted": with_deleted}
        return super().get_by_id(_id=guardrail_id, query_params=query_params, **kwargs)

    def get(
        self,
        search: Optional[str] = None,
        ids: Optional[set[UUID]] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=25)] = None,
        with_deleted: bool = False,
        **kwargs,
    ) -> Page:
        """
        Gets guardrails. Filter if any of the parameters are provided.

        Args:
            search (str, optional): The search query.
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            with_deleted: Whether to include deleted guardrails.
        Returns:
            Page: A page of guardrails.
        """

        query_params = {
            k: v
            for k, v in dict(
                search=search,
                page=page,
                size=size,
                ids=ids,
                with_deleted=with_deleted,
            ).items()
            if v is not None
        }

        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            query_params=query_params,
            collection_formats={"ids": "multi"},
            **kwargs,
        )

    def update(
        self,
        guardrail_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> Guardrail:
        """
        Update a guardrail.

        Args:
            guardrail_id: The id of the guardrail.
            name: The name of the guardrail.
            description: The description of the guardrail.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The updated guardrail.
        """

        payload = {
            "name": name,
            "description": description,
        }
        data = {k: v for k, v in payload.items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            entity_id=guardrail_id,
            data=data,
            **kwargs,
        )

    def delete(
        self,
        guardrail_id: str,
        **kwargs,
    ) -> None:
        """
        Delete a guardrail.

        Args:
            guardrail_id: The id of the guardrail.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            None
        """
        return super().delete(_id=guardrail_id, **kwargs)

    def run_guardrules(
        self,
        tag: Literal["input", "output"],
        guardrules: GuardRules,
        query: str,
        **kwargs,
    ) -> GuardrailValidationResponses:
        """
        Validate guards on a given input query.

        Args:
            tag: The query type.
            guardrules: The guardrules to validate.
            query: The query to validate.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The validation of each guardrule.
        """
        response_types_map = {
            "200": GuardrailValidationResponse,
            "401": "HTTPUnauthorized",
            "422": "HTTPValidationError",
        }
        payload = {
            "tag": tag,
            "guardrules": [guardrule.model_dump() for guardrule in guardrules],
            "query": query,
        }

        return self.api_client.post(
            resource_path=self._resource_path + "/run",
            model_name="guardrail_run",
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def validate_guardrules(
        self,
        guardrules: GuardRules,
        **kwargs,
    ) -> GuardrailValidationResponses:
        """
        Validate guards on a given input query.

        Args:
            guardrules: The guardrules to validate.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The validation of each guardrule.
        """
        response_types_map = {
            "200": GuardrailValidationResponse,
            "401": "HTTPUnauthorized",
            "422": "HTTPValidationError",
        }
        payload = {
            "guardrules": [guardrule.model_dump() for guardrule in guardrules],
        }

        return self.api_client.post(
            resource_path=self._resource_path + "/validate",
            model_name="guardrail_validate",
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def gardrules_types(self, **kwargs) -> list[str]:
        """
        Get the types of the available guardrules.

        Returns:
            A list of available guardrule types.
        """
        schemas = self.gardrules_schema(**kwargs)
        return [
            schema["properties"]["type"]["const"]
            for schema in schemas
            if schema.get("properties", {}).get("type", {}).get("const") is not None
        ]

    def gardrules_schema(self, **kwargs) -> list[dict]:
        """
        Get the schema of the available guardrules.

        Returns:
            A list of available guardrule schemas.
        """
        response_types_map = {
            "200": "object",
            "401": "HTTPUnauthorized",
        }

        header_params = kwargs.pop("_headers", {}).copy()
        header_params["Accept"] = self.api_client.select_header_accept(["application/json"])
        auth_settings = ["implicit"]

        return self.api_client.call_api(
            resource_path=f"{self._resource_path}/schema",
            method="GET",
            header_params=header_params,
            query_params={},
            auth_settings=auth_settings,
            response_types_map=response_types_map,
            **kwargs,
        )

    def create_version(
        self,
        guardrail_id: str,
        name: str,
        guardrules: GuardRules,
        description: str | None = None,
        **kwargs,
    ) -> GuardrailVersion:
        """
        Create a new guardrail version.

        Args:
            guardrail_id: The id of the guardrail.
            name: The name of the guardrail version.
            description: The description of the guardrail version.
            guardrules: The rules of the guardrail version.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The created guardrail version.
        """
        response_types_map = {
            "201": self._model_version_class,
            "401": "HTTPUnauthorized",
            "404": "HTTPNotFound",
            "422": "HTTPValidationError",
        }
        payload = {
            "name": name,
            "guardrules": [rule.model_dump() for rule in guardrules],
        }
        if description is not None:
            payload["description"] = description
        return self.api_client.post(
            resource_path=f"{self._resource_path}/{guardrail_id}/versions",
            model_name=self._model_version_name,
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def get_versions(
        self,
        guardrail_id: str,
        ids: Optional[set[UUID]] = None,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        with_deleted: bool = False,
        **kwargs,
    ) -> list[GuardrailVersion]:
        """
        Gets guardrail versions. Filter if any of the parameters are provided.

        Args:
            guardrail_id: The id of the guardrail.
            ids: The ids of the guardrail versions.
            name: The name of the guardrail version.
            created_by: The creator of the guardrail version.
            with_deleted: Whether to include versions of deleted guardrails.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            List[GuardrailVersion]: A list of guardrail versions.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name, created_by=created_by, ids=ids, guardrail_id=guardrail_id, with_deleted=with_deleted
            ).items()
            if v is not None
        }

        return self.api_client.get(
            resource_path=f"{self._resource_path}/versions",
            model_name=self._model_version_name,
            model_class=self._model_version_class,
            query_params=query_params,
            paginate=False,
            collection_formats={"ids": "multi"},
            **kwargs,
        )

    def update_version(
        self,
        id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs,
    ) -> GuardrailVersion:
        """
        Update a guardrail version.

        Args:
            id: The id of the guardrail version.
            name: The name of the guardrail version.
            description: The description of the guardrail version.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The updated guardrail version.
        """

        payload = {
            "name": name,
            "description": description,
        }
        data = {k: v for k, v in payload.items() if v is not None}
        return self.api_client.update(
            resource_path=f"{self._resource_path}/versions",
            model_name=self._model_version_name,
            model_class=self._model_version_class,
            entity_id=id,
            data=data,
            **kwargs,
        )

    def run_versions(
        self,
        tag: Literal["input", "output"],
        ids: set[UUID],
        query: str,
        **kwargs,
    ) -> GuardrailValidationResponses:
        """
        Validate guardrules on a given input query.

        Args:
            tag: The tag of the guardrail.
            ids: The ids of the guardrail versions to validate.
            query: The input query to validate.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The validation of each guardrule.
        """
        response_types_map = {
            "200": GuardrailValidationResponse,
            "401": "HTTPUnauthorized",
            "422": "HTTPValidationError",
        }
        payload = {
            "tag": tag,
            "guardrail_version_ids": ids,
            "query": query,
        }

        return self.api_client.post(
            resource_path=self._resource_path + "/versions/run",
            model_name="guardrail_version_validation",
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    def add_tags(
        self,
        guardrail_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Add tags to an guardrail.

        Args:
            guardrail_id (str): The id of the guardrail.
            tag_ids list(str): List of tag ids to add the guardrail
        Returns:
            None
        """
        return self.api_client.post(
            resource_path=self._resource_path + f"/{guardrail_id}/tags",
            data=tag_ids,
            **kwargs,
        )

    def remove_tags(
        self,
        guardrail_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Delete tags from an guardrail.

        Args:
            guardrail_id (str): The id of the guardrail.
            tag_ids list(str): List of tag ids to remove from the guardrail
        Returns:
            None
        """
        return self.api_client.delete(
            resource_path=self._resource_path + "/{guardrail_id}/tags",
            model_name=self._model_name,
            entity_id=guardrail_id,
            path_params={"guardrail_id": guardrail_id},
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
        Searches for guardrails based on a prefix.

        Args:
            filters (list[Any]): Filter on db columns, list of tuples.
                e.g. [[["id", "eq", "5c05dc9f-f04a-4ce8-9d57-2ec63ee76aac"], "and", ["description", "ilike", "Construction"]], "or", ["name", "ilike", "active"]]
            search (str): Free text search on searchable fields
            sort_by (str): Field to sort by
            sort_direction (Literal["asc", "desc"]): Sort direction (ascending or descending)
            query_params can be passed as part of the kwargs for pagination

        Returns:
            Page: A page of guardrails.
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
