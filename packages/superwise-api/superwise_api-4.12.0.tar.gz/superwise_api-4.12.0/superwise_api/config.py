from typing import Optional

from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    use_hosted_auth: bool = Field(default=False, alias="SUPERWISE_USE_HOSTED_AUTH")
    hosted_auth_url: str = Field(default="https://auth.managed.superwise.ai", alias="SUPERWISE_HOSTED_AUTH_URL")
    client_id: str = Field(..., alias="SUPERWISE_CLIENT_ID", alias_priority=2)
    client_secret: str = Field(..., alias="SUPERWISE_CLIENT_SECRET")
    api_host: str = Field(default="https://api.superwise.ai", alias="SUPERWISE_API_HOST")
    auth_host: str = Field(default="https://authentication.superwise.ai", alias="SUPERWISE_AUTH_HOST")
    auth_endpoint: str = Field(default="/identity/resources/auth/v1/api-token", alias="SUPERWISE_AUTH_ENDPOINT")
    auth_url: Optional[str] = Field(default=None)

    def __init__(self, **kwargs):
        init_values = kwargs
        for key, val in self.model_fields.items():
            if hasattr(val, "alias") and val.alias:
                v = kwargs.get(key)
                if v is not None:
                    init_values[val.alias] = kwargs.get(key)
        super().__init__(**init_values)

    @field_validator("auth_host", mode="before")
    @classmethod
    def check_if_hosted(cls, v, values):
        if values.data["use_hosted_auth"]:
            return values.data["hosted_auth_url"]
        return v

    @model_validator(mode="after")
    def build_auth_url(self):
        self.auth_url = f"{self.auth_host}{self.auth_endpoint}"
        return self
