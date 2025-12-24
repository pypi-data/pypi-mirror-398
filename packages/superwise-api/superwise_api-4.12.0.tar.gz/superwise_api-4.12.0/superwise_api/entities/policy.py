from typing import Optional
from typing import Union
from typing import Any
from typing import Literal

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.policy.policy import AlertOnStatusDirection
from superwise_api.models.policy.policy import DataConfigBase
from superwise_api.models.policy.policy import DataConfigDistributionCompare
from superwise_api.models.policy.policy import DataConfigStatistics
from superwise_api.models.policy.policy import MovingAverageThresholdSettings
from superwise_api.models.policy.policy import Policy
from superwise_api.models.policy.policy import StaticThresholdSettings
from superwise_api.models.utils import SearchParams


class PolicyApi(BaseApi):
    _model_name = "policy"
    _resource_path = "/v1/policies"
    _model_class = Policy

    def create(
        self,
        name: str,
        data_config: Union[DataConfigStatistics, DataConfigDistributionCompare],
        cron_expression: str,
        threshold_settings: Union[StaticThresholdSettings, MovingAverageThresholdSettings],
        alert_on_status: AlertOnStatusDirection,
        alert_on_policy_level: bool,
        dataset_id: str,
        destination_ids: list[str],
        initialize_with_historic_data: bool = False,
        dataset_b_id: str = None,
        **kwargs,
    ) -> Policy:
        """
        Create a new policy.

        Args:
            name: The name of the policy.
            data_config: The data configuration for the policy.
            cron_expression: The cron expression that defines the schedule of the policy.
            threshold_settings: The threshold settings for the policy.
            alert_on_status: The direction of the alert.
            alert_on_policy_level: Whether to alert on policy level.
            dataset_id: The dataset id.
            destination_ids: The destination ids.
            initialize_with_historic_data: If true, the policy will be initialized with historic data
            dataset_b_id: The second dataset this policy is monitoring.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The created policy.
        """
        data = {
            k: v
            for k, v in dict(
                name=name,
                data_config=data_config,
                cron_expression=cron_expression,
                threshold_settings=threshold_settings,
                alert_on_status=alert_on_status,
                alert_on_policy_level=alert_on_policy_level,
                dataset_id=dataset_id,
                destination_ids=destination_ids,
                initialize_with_historic_data=initialize_with_historic_data,
                dataset_b_id=dataset_b_id,
            ).items()
            if v is not None
        }
        return self.api_client.create(
            resource_path=self._resource_path, model_name=self._model_name, model_class=Policy, data=data, **kwargs
        )

    def get_by_id(self, policy_id: str, **kwargs) -> Policy:
        """
        Gets a policy by id.

        Args:
            policy_id (str): The id of the policy.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Policy: The retrieved policy.
        """
        return super().get_by_id(_id=policy_id, **kwargs)

    def get(
        self,
        name: Optional[str] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        dataset_id: Optional[str] = None,
        page: Optional[int] = None,
        size: Optional[int] = None,
        **kwargs,
    ) -> Page:
        """
        Gets policies. Filter if any of the parameters are provided.

        Args:
            name (str, optional): The name of the policy.
            status (str, optional): The status of the policy.
            created_by (str, optional): The creator of the policy.
            dataset_id (str, optional): The id of the dataset.
            page (int, optional): The page number.
            size (int, optional): The size of the page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of policies.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name, status=status, created_by=created_by, dataset_id=dataset_id, page=page, size=size
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Policy,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        policy_id: str,
        *,
        name: Optional[str] = None,
        data_config: Optional[DataConfigBase] = None,
        cron_expression: Optional[str] = None,
        destination_ids: Optional[list[str]] = None,
        alert_on_status: Optional[AlertOnStatusDirection] = None,
        alert_on_policy_level: Optional[bool] = None,
        dataset_id: Optional[str] = None,
        threshold_settings: Optional[Union[StaticThresholdSettings, MovingAverageThresholdSettings]] = None,
        initialize_with_historic_data: Optional[bool] = None,
        **kwargs,
    ) -> Policy:
        """
        Update a policy.

        Args:
            policy_id: The id of the policy.
            name: The name of the policy.
            data_config: The data configuration for the policy.
            cron_expression: The cron expression that defines the schedule of the policy.
            threshold_settings: The threshold settings for the policy.
            alert_on_status: The direction of the alert.
            alert_on_policy_level: Whether to alert on policy level.
            dataset_id: The dataset id.
            destination_ids: The destination ids.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The updated policy.
        """
        if not any(
            [
                name,
                data_config,
                cron_expression,
                threshold_settings,
                alert_on_status,
                alert_on_policy_level,
                dataset_id,
                destination_ids,
            ]
        ):
            raise ValueError("At least one parameter must be provided to update the policy.")

        data = {
            k: v
            for k, v in dict(
                name=name,
                data_config=data_config,
                cron_expression=cron_expression,
                destination_ids=destination_ids,
                alert_on_status=alert_on_status,
                alert_on_policy_level=alert_on_policy_level,
                dataset_id=dataset_id,
                threshold_settings=threshold_settings,
                initialize_with_historic_data=initialize_with_historic_data,
            ).items()
            if v is not None
        }
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Policy,
            entity_id=policy_id,
            data=data,
            **kwargs,
        )

    def delete(self, policy_id: str, **kwargs):
        """
        Deletes a policy.

        Args:
            policy_id (str): The id of the policy to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return super().delete(_id=policy_id, **kwargs)

    @BaseApi.raise_exception
    def trigger(self, policy_id: str, **kwargs):
        """
        Trigger a policy.

        Args:
            policy_id (str): The id of the policy to trigger.
            **kwargs: Arbitrary keyword arguments.
        """
        return self.api_client.post(
            resource_path=f"{self._resource_path}/{policy_id}/trigger",
            **kwargs,
        )

    def add_tags(
        self,
        policy_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Add tags to an policy.

        Args:
            policy_id (str): The id of the policy.
            tag_ids list(str): List of tag ids to add the policy
        Returns:
            None
        """
        return self.api_client.post(
            resource_path=self._resource_path + f"/{policy_id}/tags",
            data=tag_ids,
            **kwargs,
        )

    def remove_tags(
        self,
        policy_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Delete tags from an policy.

        Args:
            policy_id (str): The id of the policy.
            tag_ids list(str): List of tag ids to remove from the policy
        Returns:
            None
        """
        return self.api_client.delete(
            resource_path=self._resource_path + "/{policy_id}/tags",
            model_name=self._model_name,
            entity_id=policy_id,
            path_params={"policy_id": policy_id},
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
        Searches for policies based on a prefix.

        Args:
            filters (list[Any]): Filter on db columns, list of tuples.
                e.g. [[["id", "eq", "5c05dc9f-f04a-4ce8-9d57-2ec63ee76aac"], "and", ["description", "ilike", "Construction"]], "or", ["name", "ilike", "active"]]
            search (str): Free text search on searchable fields
            sort_by (str): Field to sort by
            sort_direction (Literal["asc", "desc"]): Sort direction (ascending or descending)
            query_params can be passed as part of the kwargs for pagination


        Returns:
            Page: A page of policies.
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
