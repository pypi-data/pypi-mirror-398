from functools import wraps

from superwise_api.client.api_client import ApiClient
from superwise_api.client.exceptions import ApiAttributeError
from superwise_api.client.exceptions import ApiException
from superwise_api.client.exceptions import ApiKeyError
from superwise_api.client.exceptions import ApiTypeError
from superwise_api.client.exceptions import ApiValueError
from superwise_api.errors import SuperwiseApiException


class BaseApi:
    _resource_path = None
    _model_name = None
    _model_class = None

    def __init__(self, api_client: ApiClient):
        """
        Initializes the Api class.

        Args:
            api_client (ApiClient): An instance of the SuperwiseApiClient to make requests.
        """
        self.api_client = api_client
        self.wrap_api_calls()

    def wrap_api_calls(self):
        for method_name in dir(self):
            method = getattr(self, method_name)
            if callable(method) and method_name in ["put", "update", "create", "get", "get_by_id", "delete"]:
                setattr(self, method_name, self.raise_exception(method))

    @staticmethod
    def raise_exception(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApiException as e:
                raise SuperwiseApiException(original_exception=e, message=e.body)
            except (ApiTypeError, ApiValueError, ApiAttributeError, ApiKeyError) as e:
                raise e
            except Exception as e:
                raise SuperwiseApiException(e, message="A general error occurred - We are looking into it")

        return wrapper

    def get_by_id(self, _id: str, **kwargs):
        """
        Retrieves an entity by its id.

        Args:
            _id (str): The id of the entity to retrieve.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Source: The retrieved entity.
        """
        return self.api_client.get_by_id(
            resource_path=self._resource_path,
            model_name=self._model_name,
            model_class=self._model_class,
            entity_id=_id,
            **kwargs,
        )

    def delete(self, _id: str, **kwargs):
        """
        Deletes an entity.

        Args:
            _id (str): The id of the entity to delete.
            **kwargs: Arbitrary keyword arguments.
        """
        return self.api_client.delete(
            resource_path=self._resource_path, model_name=self._model_name, entity_id=_id, **kwargs
        )
