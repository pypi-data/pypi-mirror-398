import json
import pprint

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic_core import to_jsonable_python


class SuperwiseEntity(BaseModel):
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        return json.dumps(self.model_dump(), default=to_jsonable_python)

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        return self.model_dump(by_alias=True, exclude={}, exclude_none=True)

    @classmethod
    def from_dict(cls, obj: dict):
        return cls.model_validate(obj) if obj else None

    @classmethod
    def from_json(cls, json_str: str):
        """Create an instance of DatasetResponse from a JSON string"""
        return cls.from_dict(json.loads(json_str))
