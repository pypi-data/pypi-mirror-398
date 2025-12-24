from typing import Optional
from typing import Sequence
from typing import Any
from typing import Literal

from pydantic import conint

from superwise_api.client.api_client import ApiClient
from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.agent.agent import AgentConfig, Version, ExtendedAgent
from superwise_api.models.agent.agent import Agent
from superwise_api.models.agent.agent import ModelLLM
from superwise_api.models.agent.agent import ToolDef
from superwise_api.models.agent.flowise import FlowiseCredentialUserInput
from superwise_api.models.agent.playground import AskResponsePayload
from superwise_api.models.dataset.dataset import Dataset
from superwise_api.models.agent.feedback import EventFeedbackData
from superwise_api.models.utils import SearchParams


class AgentApi(BaseApi):
    """
    This class provides methods to interact with the Agent API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
    """

    _model_name = "agent"
    _resource_path = "/v1/agents"
    _model_class = Agent

    def __init__(self, api_client: ApiClient) -> None:
        """
        Initializes the DatasetApi class.

        Args:
            api_client (ApiClient): An instance of the SuperwiseApiClient to make requests.
        """
        super().__init__(api_client)
        self._playground_resource_path = "/v1/application-playground"

    def create(
        self,
        name: str,
        description: str = None,
        authentication_enabled: bool = False,
        observability_enabled: bool = True,
        block_guardrails_violations: bool = True,
        guardrails_violation_message: str | None = None,
        **kwargs,
    ) -> Agent:
        """
        Creates a new agent.

        Args:
            name (str): The name of the agent.
            description (str): The agent's description.
            authentication_enabled (bool): Whether the agent requires an api token for access or not.
            observability_enabled (bool): Whether the agent logs conversation to the db or not.

        Returns:
            Agent: The created agent.
        """

        payload = {
            "name": name,
            "authentication_enabled": authentication_enabled,
            "observability_enabled": observability_enabled,
            "block_guardrails_violations": block_guardrails_violations,
        }
        if description:
            payload["description"] = description
        if guardrails_violation_message:
            payload["guardrails_violation_message"] = guardrails_violation_message
        return self.api_client.create(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Agent,
            data=payload,
            **kwargs,
        )

    def create_version(
        self,
        agent_id: str,
        name: str,
        agent_config: AgentConfig,
        guardrails: list[str] = None,
        description: str = None,
        **kwargs,
    ) -> Version:
        """
        Creates a new version for the agent.

        Args:
            agent_id (str): The id of the agent.
            name (str): The name of the version.
            description (str): The version's description.
            agent_config (AgentConfig): agent configuration for this version.
            guardrails: set(str): set of guardrails ids to apply to this version.

        Returns:
            Version: The created version.
        """

        payload = {
            "name": name,
            "agent_config": agent_config,
            "guardrails": guardrails if guardrails else [],
        }
        if description:
            payload["description"] = description
        return self.api_client.create(
            resource_path=self._resource_path + f"/{agent_id}/versions",
            model_name=self._model_name,
            model_class=Version,
            data=payload,
            **kwargs,
        )

    def update(
        self,
        agent_id: str,
        name: str | None = None,
        description: str | None = None,
        authentication_enabled: bool | None = None,
        observability_enabled: bool | None = None,
        block_guardrails_violations: bool | None = None,
        guardrails_violation_message: str | None = None,
        dataset_id: str | None = None,
        **kwargs,
    ) -> Agent:
        """
        Updates the agent.

        Args:
            agent_id (str): The id of the agent.
            name (str, optional): The new name of the agent.
            description (str, optional): Description for the agent.
            authentication_enabled (bool, optional): Whether the agent requires an api token for access or not.
            observability_enabled (bool, optional): Whether the agent logs conversation to the db or not.
            block_guardrails_violations (bool, optional): Whether to block guardrails violations.
            guardrails_violation_message (str, optional): The message to show when guardrails are violated.
            dataset_id (str, optional): The id of the dataset to associate with the agent.

        Returns:
            Agent: The updated agent.
        """

        payload = {
            "name": name,
            "description": description,
            "authentication_enabled": authentication_enabled,
            "observability_enabled": observability_enabled,
            "block_guardrails_violations": block_guardrails_violations,
            "guardrails_violation_message": guardrails_violation_message,
            "dataset_id": dataset_id,
        }
        data = {k: v for k, v in payload.items() if v is not None}
        if len(data) == 0:
            raise ValueError("At least one parameter must be provided to update the agent.")
        return self.api_client.update(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Agent,
            entity_id=agent_id,
            data=data,
            **kwargs,
        )

    def update_version(
        self,
        version_id: str,
        agent_id: str,
        name: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> Version:
        """
        Updates the agent's version.

        Args:
            version_id (str): The version's id.
            agent_id (str): The id of the version's agent.
            name (str, optional): The new name of the version.
            description (str, optional): New description for the version.

        Returns:
            Version: The updated version.
        """

        payload = {"name": name, "description": description}
        data = {k: v for k, v in payload.items() if v is not None}
        if len(data) == 0:
            raise ValueError("At least one parameter must be provided to update the version.")
        return self.api_client.update(
            resource_path=self._resource_path + "/{agent_id}/versions/{version_id}",
            model_name=self._model_name,
            model_class=Version,
            entity_id=agent_id,
            data=data,
            path_params={"agent_id": agent_id, "version_id": version_id},
            **kwargs,
        )

    def get_version_by_id(self, agent_id: str, version_id: str, **kwargs) -> Version:
        """
        Retrieves an entity by its id.

        Args:
            agent_id (str): The id of the agent.
            version_id (str): The id of the version to retrieve.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Source: The retrieved entity.
        """
        return self.api_client.get_by_id(
            resource_path=self._resource_path + f"/{agent_id}/versions/{version_id}",
            model_name="version",
            model_class=Version,
            entity_id=version_id,
            path_params={"agent_id": agent_id, "version_id": version_id},
            **kwargs,
        )

    def get_versions(
        self, agent_id: str, name: Optional[str] = None, created_by: Optional[str] = None, **kwargs
    ) -> list[Version]:
        """
        Retrieves agent entities.

        Args:
            agent_id (str): The id of the agent.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            list[Version]: The retrieved entities.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name,
                created_by=created_by,
            ).items()
            if v is not None
        }

        return self.api_client.get(
            resource_path=self._resource_path + f"/{agent_id}/versions",
            model_name="version",
            model_class=Version,
            query_params=query_params,
            paginate=False,
            **kwargs,
        )

    def get(
        self,
        name: Optional[str] = None,
        created_by: Optional[str] = None,
        prompt: Optional[str] = None,
        dataset_id: Optional[str] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=1)] = None,
        **kwargs,
    ) -> Page:
        """
        Gets agents. Filter if any of the parameters are provided.

        Args:
            name (str, optional): The name of the agent.
            created_by (str, optional): The creator of the agent.
            prompt (str, optional): The prompt of the agent.
            dataset_id (str, optional): The id of the dataset.
            page (int, optional): The page number.
            size (int, optional): The size of the page.

        Returns:
            Page: A page of agents.
        """

        query_params = {
            k: v
            for k, v in dict(
                name=name,
                created_by=created_by,
                prompt=prompt,
                dataset_id=dataset_id,
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=Agent,
            query_params=query_params,
            **kwargs,
        )

    @BaseApi.raise_exception
    def test_model_connection(self, llm_model: ModelLLM, **kwargs):
        """
        Tests the connection to the model. Raises exception on fail.

        Args:
            llm_model (ModelLLM): The model to test.
        """
        response_types_map = {"204": None, "422": "HTTPValidationError"}
        return self.api_client.post(
            resource_path=self._resource_path + "/test-model-connection",
            data=llm_model.model_dump(),
            response_types_map=response_types_map,
            **kwargs,
        )

    @BaseApi.raise_exception
    def test_tool_connection(self, tool: ToolDef, **kwargs):
        """
        Tests the connection to the tool. Raises exception on fail.

        Args:
            tool (ToolDef): The tool to test.
        """
        response_types_map = {"204": None, "422": "HTTPValidationError"}
        return self.api_client.post(
            resource_path=self._resource_path + "/test-tool-connection",
            data=tool.model_dump(),
            response_types_map=response_types_map,
            **kwargs,
        )

    @BaseApi.raise_exception
    def ask_playground(
        self, input: str, agent_config: AgentConfig, chat_history: Optional[Sequence[dict]] = None, **kwargs
    ) -> AskResponsePayload:
        """
        Performs ask request in playground mode.

        Args:
            input (str): The input to the model.
            agent_config (AgentConfig): The type of the agent and connected tools/context.
            chat_history (Sequence[dict], optional): The chat history.

        Returns:
            AskResponsePayload: The response payload.
        """
        payload = {
            "config": agent_config,
            "input": input,
            "chat_history": chat_history or [],
        }
        response_types_map = {"200": AskResponsePayload, "422": "HTTPValidationError"}
        return self.api_client.post(
            resource_path=self._playground_resource_path + "/ask",
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    @BaseApi.raise_exception
    def ask_worker(
        self,
        agent_id: str,
        input: str,
        api_token: str | None = None,
        chat_history: Optional[Sequence[dict]] = None,
        context_id: str | None = None,
        **kwargs,
    ) -> AskResponsePayload:
        """
        Performs ask request to the specified worker.

        Args:
            agent_id (str): The agent asked.
            input (str): The input to the model.
            api_token (str): The API token of the agent.
            chat_history (Sequence[dict], optional): The chat history.

        Returns:
            AskResponsePayload: The response payload.
        """
        payload = {
            "input": input,
            "chat_history": chat_history or [],
            "context_id": context_id,
        }
        headers = {"x-api-token": api_token} if api_token else {}
        response_types_map = {"200": AskResponsePayload, "422": "HTTPValidationError"}
        return self.api_client.post(
            resource_path=f"/v1/app-worker/{agent_id}/v1/ask",
            data=payload,
            response_types_map=response_types_map,
            _headers=headers,
            **kwargs,
        )

    def get_flowise_credential_schema(self, url: str, api_key: str, flow_id, **kwargs) -> FlowiseCredentialUserInput:
        """
        Get credential schema.

        Args:
            url (str): url to the flowise agent.
            api_key (str): Flow-relevant API key.
            flow_id (str): ID of the requested flow.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            FlowiseCredentialUserInput: Required schema of the credentials.
        """
        payload = {
            "url": url,
            "api_key": api_key,
            "flow_id": flow_id,
        }
        response_types_map = {
            "200": FlowiseCredentialUserInput,
            "404": None,
            "422": None,
            "500": None,
        }
        return self.api_client.post(
            resource_path=self._resource_path + "/credential-schema",
            model_name=self._model_name,
            data=payload,
            response_types_map=response_types_map,
            **kwargs,
        )

    @BaseApi.raise_exception
    def regenerate_api_key(self, agent_id: str, **kwargs) -> Agent:
        """
        Regenerates api key for agent.

        Args:
            agent_id (str): The agent asked.
        Returns:
            Agent: Agent with the new api key.
        """
        response_types_map = {"200": Agent, "422": "HTTPValidationError"}
        return self.api_client.post(
            resource_path=self._resource_path + f"/{agent_id}/regenerate",
            response_types_map=response_types_map,
            **kwargs,
        )

    def create_dataset(self, agent_id: str, name: str, **kwargs) -> Dataset:
        """
        Creates a new dataset for the agent.

        Args:
            agent_id (str): The id of the agent.
            name (str): The name of the version.

        Returns:
            Dataset: The created dataset.
        """

        payload = {
            "name": name,
        }
        return self.api_client.create(
            resource_path=self._resource_path + f"/{agent_id}/create-dataset",
            model_name=self._model_name,
            model_class=Dataset,
            data=payload,
            **kwargs,
        )

    @BaseApi.raise_exception
    def send_feedback(
        self,
        agent_id: str,
        payload: EventFeedbackData,
        api_token: str | None = None,
        **kwargs,
    ) -> None:
        """
        Sends feedback to the specified worker for its answer.

        Args:
            agent_id (str): The agent receiving the feedback.
            payload (EventFeedbackData): The feedback payload.
            api_token (str): The API token of the application.
        Returns:
            None
        """
        headers = {"x-api-token": api_token} if api_token else {}
        response_types_map = {
            "200": None,
            "422": "HTTPValidationError",
            "401": "HTTPUnauthorized",
            "500": None,
        }

        self.api_client.post(
            resource_path=f"/v1/app-worker/{agent_id}/v1/feedback",
            data=payload,
            response_types_map=response_types_map,
            _headers=headers,
            **kwargs,
        )

    @BaseApi.raise_exception
    def verify_dataset_schema(self, dataset_id: str, **kwargs) -> bool:
        """
        Verifies that the dataset schema matches the expected agent dataset schema or is a superset of it.

        Args:
            dataset_id (str): The id of the dataset to verify.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if the schema matches, False otherwise.
        """
        response_types_map = {
            "200": bool,
            "404": None,
            "500": None,
        }
        return self.api_client.post(
            resource_path=f"{self._resource_path}/verify-dataset-schema/{dataset_id}",
            response_types_map=response_types_map,
            **kwargs,
        )

    def add_tags(
        self,
        agent_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Add tags to an agent.

        Args:
            agent_id (str): The id of the agent.
            tag_ids list(str): List of tag ids to add the agent
        Returns:
            None
        """
        return self.api_client.post(
            resource_path=self._resource_path + f"/{agent_id}/tags",
            data=tag_ids,
            **kwargs,
        )

    def remove_tags(
        self,
        agent_id: str,
        tag_ids: list[str],
        **kwargs,
    ):
        """
        Delete tags from an agent.

        Args:
            agent_id (str): The id of the agent.
            tag_ids list(str): List of tag ids to remove from the agent
        Returns:
            None
        """
        return self.api_client.delete(
            resource_path=self._resource_path + "/{agent_id}/tags",
            model_name=self._model_name,
            entity_id=agent_id,
            path_params={"agent_id": agent_id},
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
        Searches for agents based on a prefix.

        Args:
            filters (list[Any]): Filter on db columns, list of tuples.
                e.g. [[["id", "eq", "5c05dc9f-f04a-4ce8-9d57-2ec63ee76aac"], "and", ["description", "ilike", "Construction"]], "or", ["name", "ilike", "active"]]
            search (str): Free text search on searchable fields
            sort_by (str): Field to sort by
            sort_direction (Literal["asc", "desc"]): Sort direction (ascending or descending)
            query_params can be passed as part of the kwargs for pagination

        Returns:
            Page: A page of enriched agents.
        """
        data = SearchParams(
            filters=filters,
            search=search,
            sort_by=sort_by,
            sort_direction=sort_direction,
        ).model_dump(exclude_none=True)
        response_types_map = {
            "200": Page.set_model(ExtendedAgent),
            "422": None,
            "500": None,
        }
        return self.api_client.post(
            resource_path="/v1/enriched-agents/search",
            data=data,
            response_types_map=response_types_map,
            **kwargs,
        )
