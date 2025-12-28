from marshmallow import fields as marshmallow_fields

from s4.platform.internal.base_schema import BaseSchema


class FromPoolConfig(object):
    def __init__(
        self, *, pool_pattern: str, original_input_pattern: str, level: int = 0
    ):
        self.pool_pattern = pool_pattern
        self.level = level
        self.original_input_pattern = original_input_pattern


class FromPoolConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FromPoolConfig, **kwargs)

    pool_pattern = marshmallow_fields.Str()
    level = marshmallow_fields.Int()
    original_input_pattern = marshmallow_fields.Str()
