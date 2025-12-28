from typing import Optional

from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.fields_mixin import BaseFieldValue


class FieldValue(BaseFieldValue):
    def __init__(self, *, value: Optional[str] = None,
                 data_type: str,
                 validation_errors: Optional[list[str]] = None,
                 overridden: Optional[bool] = False,
                 values: Optional[list[str]] = None):
        self.value = value
        self.data_type = data_type
        self.validation_errors = validation_errors
        self.overridden = overridden
        self.values = values


class FieldValueSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FieldValue, **kwargs)

    value = fields.Str(required=False, allow_none=True)
    data_type = fields.Str(required=True)
    validation_errors = fields.List(fields.Str(), allow_none=True)
    overridden = fields.Bool(required=False, allow_none=True)
    values = fields.List(fields.Str(), allow_none=True)
