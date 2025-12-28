from marshmallow import fields
from s4.platform.internal.camel_case_schema import CamelCaseSchema


class ProspectiveTaskFunctionSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    is_running = fields.Bool()


class ProspectiveTaskFunction:
    def __init__(self, *, is_running: bool):
        self.is_running = is_running


class FunctionListSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    functions = fields.Dict(
        keys=fields.Str, values=fields.Nested(ProspectiveTaskFunctionSchema)
    )


class FunctionList:
    def __init__(self, *, functions: dict[str, ProspectiveTaskFunction]):
        self.functions = functions
