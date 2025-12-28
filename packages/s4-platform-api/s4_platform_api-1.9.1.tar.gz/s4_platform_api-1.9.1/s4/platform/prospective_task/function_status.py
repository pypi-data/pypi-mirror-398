from marshmallow import fields
from typing import Optional

from s4.platform.internal.base_schema import BaseSchema


class FunctionResult:
    def __init__(self, *, status: int, message: str):
        self.status = status
        self.message = message


class FunctionStatus:
    def __init__(
        self, *, name: str, is_running: bool, result: Optional[FunctionResult] = None
    ):
        self.name = name
        self.is_running = is_running
        self.result = result


class FunctionResultSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FunctionResult, **kwargs)

    status = fields.Int()
    message = fields.Str()


class FunctionStatusSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FunctionStatus, **kwargs)

    name = fields.Str()
    is_running = fields.Bool()
    result = fields.Nested(FunctionResultSchema, allow_none=True)
