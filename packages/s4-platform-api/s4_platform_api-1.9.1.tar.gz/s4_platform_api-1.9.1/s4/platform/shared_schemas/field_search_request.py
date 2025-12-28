from typing import Optional

from marshmallow import fields
from s4.platform.internal.camel_case_schema import CamelCaseSchema


class FieldSearchRequestSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    operator = fields.String()
    value = fields.String()
    data_type = fields.String()


class FieldSearchRequest:
    def __init__(self, *, operator: str, value: str, data_type: Optional[str] = None):
        self.operator = operator
        self.value = value
        self.data_type = data_type
