from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
from pydantic import RootModel

from superwise_api.models import SuperwiseEntity


class FlowiseCreationCredential(SuperwiseEntity):
    name: str
    credential_name: str = Field(alias="credentialName")
    plain_data_obj: dict[str, str] = Field(alias="plainDataObj")
    model_config = ConfigDict(populate_by_name=True, loc_by_alias=False)

    @model_validator(mode="before")
    def strip_constraints(cls, values):
        if isinstance(values, dict):
            values.pop("constraints", None)
        return values


class FlowiseCredentialUserInput(RootModel[dict[str, FlowiseCreationCredential]]):
    model_config = ConfigDict(populate_by_name=True, loc_by_alias=False)

    @classmethod
    def from_dict(cls, obj: dict) -> "FlowiseCredentialUserInput | None":
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return FlowiseCredentialUserInput.model_validate(obj)

        _obj = FlowiseCredentialUserInput.model_validate(
            {key: FlowiseCreationCredential.model_validate(value) for key, value in obj.items()}
        )
        return _obj

    def to_dict(self) -> dict[str, dict[str, str]]:
        return {key: value.to_dict() for key, value in self.model_dump().items()}
