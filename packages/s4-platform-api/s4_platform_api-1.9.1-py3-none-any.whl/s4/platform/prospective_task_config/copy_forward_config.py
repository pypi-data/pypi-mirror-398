from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema


class CopyForwardConfig(object):
    def __init__(self, *, pattern: str):
        self.pattern = pattern


class CopyForwardConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(CopyForwardConfig, **kwargs)

    pattern = fields.Str(required=True)

