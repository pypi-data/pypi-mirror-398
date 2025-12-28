from marshmallow import fields
from s4.platform.internal.camel_case_schema import CamelCaseSchema


class IriListSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super(IriListSchema, self).__init__(**kwargs)

    data = fields.List(fields.Str())


class EntityIriListSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super(EntityIriListSchema, self).__init__(**kwargs)

    data = fields.List(fields.Str())
    historical = fields.Bool(allow_none=True)
    before_time = fields.Str(allow_none=True)
