from typing import Optional

from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.fields_mixin import BaseFieldValue


class ProspectiveFieldValue(BaseFieldValue):
    def __init__(
        self,
        *,
        value: Optional[str] = None,
        data_type: str,
        overridden: Optional[bool] = False,
        validation_errors: Optional[list[str]] = None,
        label: Optional[str] = None,
        values: Optional[list[str]] = None,
    ) -> None:
        self.value = value
        self.data_type = data_type
        self.validation_errors = validation_errors
        self.overridden = overridden
        self.label = label
        self.values = values


class ProspectiveFieldValueSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveFieldValue, **kwargs)

    value = fields.Str(allow_none=True)
    data_type = fields.Str(required=True)
    validation_errors = fields.List(fields.Str, load_default=[], load_only=True)
    overridden = fields.Bool()
    label = fields.Str(allow_none=True)
    values = fields.List(fields.Str(), allow_none=True)
