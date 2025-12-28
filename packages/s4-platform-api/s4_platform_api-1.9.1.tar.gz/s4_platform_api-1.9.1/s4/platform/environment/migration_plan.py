from enum import Enum

from typing import Optional
from marshmallow import fields
from marshmallow_enum import EnumField

from s4.platform.internal.base_schema import BaseSchema


class MigrationAction(Enum):
    DoNothing = "DoNothing"
    SwapChangeset = "SwapChangeset"
    Move = "Move"
    Upgrade = "Upgrade"
    Revise = "Revise"
    Remove = "Remove"


class ExecutionLocation(object):
    def __init__(
        self,
        activity_id: str,
        root_process_definition_key: str,
        call_activity_chain: Optional[list[str]] = None,
    ):
        self.activity_id = activity_id
        self.root_process_definition_key = root_process_definition_key
        self.call_activity_chain = call_activity_chain


class ExecutionLocationSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ExecutionLocation, **kwargs)

    activity_id = fields.Str()
    root_process_definition_key = fields.Str()
    call_activity_chain = fields.List(fields.Str())


class MigrationInstruction(object):
    def __init__(
        self,
        source: ExecutionLocation,
        action: MigrationAction,
        destination: Optional[ExecutionLocation] = None,
    ):
        self.source = source
        self.action = action
        self.destination = destination


class MigrationInstructionSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(MigrationPlan, **kwargs)

    source = fields.Nested(ExecutionLocationSchema, allow_none=False)
    action = EnumField(MigrationAction, by_value=True)
    destination = fields.Nested(ExecutionLocationSchema, allow_none=True)


class MigrationPlan(object):
    def __init__(
        self,
        default_action: Optional[MigrationAction] = None,
        instructions: Optional[list[MigrationInstruction]] = None,
    ):
        self.default_action = default_action
        self.instructions = instructions


class MigrationPlanSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(MigrationPlan, **kwargs)

    default_action = EnumField(MigrationAction, by_value=True)
    instructions = fields.List(
        fields.Nested(MigrationInstructionSchema, allow_none=True)
    )
