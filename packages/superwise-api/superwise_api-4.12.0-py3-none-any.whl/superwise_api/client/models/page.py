# coding: utf-8
from __future__ import annotations

import json
import pprint
import re  # noqa: F401
from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import conint
from pydantic import conlist
from pydantic import Field
from pydantic import StrictInt
from pydantic import StrictStr


class Page(BaseModel):
    """
    PageDatasetResponse
    """

    __model = None
    items: conlist(BaseModel) = Field(...)
    total: Optional[StrictInt] = 0
    page: conint(strict=True, ge=1) = Field(...)
    size: conint(strict=True, ge=1) = Field(...)
    next: Optional[StrictStr] = None
    previous: Optional[StrictStr] = None
    first: Optional[StrictStr] = None
    last: Optional[StrictStr] = None
    __properties = ["items", "total", "page", "size", "next", "previous", "first", "last"]

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "json_encoders": {datetime: lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]},
    }

    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.dict(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        _dict = json.loads(self.model_dump_json(by_alias=True, exclude={}, exclude_none=True))
        # override the default output from pydantic by calling `to_dict()` of each item in items (list)
        _items = []
        if self.items:
            for _item in self.items:
                if _item:
                    _items.append(json.loads(_item.model_dump_json()))
            _dict["items"] = _items
        return json.dumps(_dict)

    @classmethod
    def from_json(cls, json_str: str) -> Page:
        """Create an instance of PageDatasetResponse from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self):
        """Returns the dictionary representation of the model using alias"""
        _dict = self.model_dump(by_alias=True, exclude={}, exclude_none=True)
        # override the default output from pydantic by calling `to_dict()` of each item in items (list)
        _items = []
        if self.items:
            for _item in self.items:
                if _item:
                    _items.append(_item.to_dict())
            _dict["items"] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: dict) -> Optional[Page]:
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return Page.model_validate(obj)

        _obj = Page.model_validate(
            {
                "items": [cls.__model.from_dict(_item) for _item in obj.get("items")]
                if obj.get("items") is not None
                else None,
                "total": obj.get("total") if obj.get("total") is not None else 0,
                "page": obj.get("page"),
                "size": obj.get("size"),
                "next": obj.get("next"),
                "previous": obj.get("previous"),
                "first": obj.get("first"),
                "last": obj.get("last"),
            }
        )
        return _obj

    @classmethod
    def set_model(cls, model: type[BaseModel]):
        cls.__model = model
        return cls
