from typing import Optional

from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task.prospective_entity import (
    ProspectiveEntity,
    ProspectiveEntitySchema,
)


class IoGroup(object):
    def __init__(
        self,
        *,
        inputs: dict[str, list[ProspectiveEntity]],
        outputs: dict[str, list[ProspectiveEntity]],
        manual: bool = False,
        label: Optional[str] = None,
        id: Optional[str] = None,
        validation_errors: Optional[list[str]] = None
    ):
        self.inputs = inputs
        self.outputs = outputs
        self.manual = manual
        self.id = id
        self.label = label
        self.validation_errors = validation_errors


class IoGroupSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(IoGroup, **kwargs)

    inputs = fields.Dict(
        keys=fields.Str, values=fields.List(fields.Nested(ProspectiveEntitySchema))
    )
    outputs = fields.Dict(
        keys=fields.Str, values=fields.List(fields.Nested(ProspectiveEntitySchema))
    )
    manual = fields.Bool(allow_none=True)
    label = fields.Str(allow_none=True)
    id = fields.Str(allow_none=True)
    validation_errors = fields.List(fields.Str, load_default=[], load_only=True)
