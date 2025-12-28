from marshmallow import fields
from s4.platform.internal.camel_case_schema import CamelCaseSchema
from s4.platform.internal.sort_direction import SortDirection


class SortOrderSchema(CamelCaseSchema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    field = fields.String()
    direction = SortDirection
    null_handling = fields.String()


class SortOrder:
    def __init__(
        self,
        *,
        field: str,
        direction: SortDirection = SortDirection.ASC,
        null_handling: str = None
    ):
        self.field = field
        self.direction = direction
        self.null_handling = null_handling
