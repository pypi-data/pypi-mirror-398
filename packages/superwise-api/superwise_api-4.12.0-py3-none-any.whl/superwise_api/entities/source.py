import json
import re
from datetime import datetime
from typing import Optional
from typing import Union

from pydantic import conint

from superwise_api.client.models.page import Page
from superwise_api.entities.base import BaseApi
from superwise_api.models.source.source import GCS_BUCKET_REGEX
from superwise_api.models.source.source import PUBSUB_TOPIC_REGEX
from superwise_api.models.source.source import S3_BUCKET_REGEX
from superwise_api.models.source.source import Source
from superwise_api.models.source.source import SourceType
from superwise_api.models.source.source import SQS_QUEUE_REGEX


class SourceApi(BaseApi):
    """
    This class provides methods to interact with the Source API.

    Attributes:
        api_client (ApiClient): An instance of the ApiClient to make requests.
        _model_name (str): The name of the model.
        _resource_path (str): The path of the resource.
    """

    _model_name = "source"
    _resource_path = "/v1/sources"
    _model_class = Source

    def create_gcs_source(
        self, name: str, bucket_name: str, pubsub_topic: str, service_account: Union[str, dict] = None, **kwargs
    ):
        """
        Creates a new GCS source.

        Args:
            name (str): The name of the source.
            bucket_name (str): The name of the GCS bucket.
            pubsub_topic (str): The name of the PubSub topic.
            service_account_file_path (str, optional): The path to the service account file.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Source: The created source.
        """
        if not re.match(GCS_BUCKET_REGEX, bucket_name):
            raise ValueError("Invalid GCS bucket name.")
        if not re.match(PUBSUB_TOPIC_REGEX, pubsub_topic):
            raise ValueError("Invalid PubSub topic.")

        data = {
            "name": name,
            "type": SourceType.GCS,
            "params": {"bucket_name": bucket_name, "topic_name": pubsub_topic},
        }

        if service_account:
            if isinstance(service_account, str):
                with open(service_account, "r") as file:
                    service_account_data = json.load(file)
            elif isinstance(service_account, dict):
                service_account_data = service_account
            else:
                raise TypeError("service_account must be either a file path string or a dictionary.")

            data["credentials"] = {"service_account": service_account_data}

        return self._create(data=data, **kwargs)

    def create_s3_source(
        self,
        name: str,
        bucket_arn: str,
        queue_arn: str,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        **kwargs,
    ):
        """
        Creates a new S3 source.

        Args:
            name (str): The name of the source.
            bucket_arn (str): The name of the S3 bucket.
            queue_arn (str): The name of the SQS queue.
            aws_access_key_id: (str, optional): The access key of the S3 bucket.
            aws_secret_access_key (str, optional): The secret key of the S3 bucket.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Source: The created source.
        """
        if not re.match(S3_BUCKET_REGEX, bucket_arn):
            raise ValueError("Invalid S3 bucket name.")
        if not re.match(SQS_QUEUE_REGEX, queue_arn):
            raise ValueError("Invalid SQS queue name.")

        data = {"name": name, "type": SourceType.S3, "params": {"bucket_arn": bucket_arn, "queue_arn": queue_arn}}

        if aws_access_key_id and aws_secret_access_key:
            data["credentials"] = {
                "aws_access_key_id": aws_access_key_id,
                "aws_secret_access_key": aws_secret_access_key,
            }

        return self._create(data=data, **kwargs)

    def _create(
        self,
        data,
        **kwargs,
    ) -> Source:
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
        created_by: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        type: Optional[SourceType] = None,
        page: Optional[conint(strict=True, ge=1)] = None,
        size: Optional[conint(strict=True, le=500, ge=1)] = None,
        **kwargs,
    ) -> Page:
        """
        Retrieves sources based on the provided filters.

        Args:
            name (Optional[str], optional): The name of the source.
            created_by (Optional[str], optional): The creator of the source.
            created_at (Optional[datetime], optional): When the source was created.
            updated_at (Optional[datetime], optional): When the source was last updated.
            type (Optional[SourceType], optional): The type of the source.
            page (Optional[conint(strict=True, ge=1)], optional): The page number to retrieve.
            size (Optional[conint(strict=True, le=500, ge=1)], optional): The number of sources to retrieve per page.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Page: A page of sources.
        """
        query_params = {
            k: v
            for k, v in dict(
                name=name,
                created_by=created_by,
                created_at=created_at,
                updated_at=updated_at,
                type=type,
                page=page,
                size=size,
            ).items()
            if v is not None
        }
        return self.api_client.get(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            query_params=query_params,
            **kwargs,
        )

    def update(
        self,
        source_id: str,
        *,
        name: Optional[str] = None,
        params: Optional[dict] = None,
        credentials: Optional[dict] = None,
        **kwargs,
    ) -> Source:
        """
        Updates a source.

        Args:
            source_id (str): The id of the source to update.
            name (str, optional): The new name of the source.
            params (dict, optional): The new parameters of the source.
            credentials (dict, optional): The new credentials of the source.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Source: The updated source.
        """
        if not any([name, params, credentials]):
            raise ValueError("At least one parameter must be provided to update the source.")

        data = {k: v for k, v in dict(name=name, params=params, credentials=credentials).items() if v is not None}
        return self.api_client.update(
            resource_path=self._resource_path,
            entity_id=source_id,
            model_name=self._model_name,
            model_class=self._model_class,
            data=data,
            **kwargs,
        )
