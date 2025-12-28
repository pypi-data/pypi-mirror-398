from marshmallow import fields
from s4.platform.internal.camel_case_schema import CamelCaseSchema


class FieldRestrictionSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    operator = fields.String()
    value = fields.String()


class FieldRestriction:
    def __init__(self, *, operator: str, value: str):
        self.operator = operator
        self.value = value
