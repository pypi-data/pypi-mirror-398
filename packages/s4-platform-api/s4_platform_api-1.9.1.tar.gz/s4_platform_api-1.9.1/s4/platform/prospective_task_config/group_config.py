from typing import List, Optional

from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task_config.from_pool_config import (
    FromPoolConfig,
    FromPoolConfigSchema,
)


class GroupConfig(object):
    def __init__(
        self,
        *,
        does_not_continue: bool = False,
        derived_from: List[str] = None,
        entity_derivations: dict[str, List[str]] = None,
        count: int = None,
        min_count: int = None,
        max_count: int = None,
        invalidate: bool = None,
        from_reference: bool = False,
        for_each: List[str] = None,
        from_pool: FromPoolConfig = None,
        revise_stowaway_samples: Optional[bool] = None,
        comment: str = None
    ):
        self.does_not_continue = does_not_continue
        self.derived_from = derived_from
        self.entity_derivations = entity_derivations
        self.count = count
        self.min_count = min_count
        self.max_count = max_count
        self.invalidate = invalidate
        self.from_reference = from_reference
        self.for_each = for_each
        self.from_pool = from_pool
        self.revise_stowaway_samples = revise_stowaway_samples
        self.comment = comment


class GroupConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(GroupConfig, **kwargs)

    does_not_continue = fields.Bool()
    derived_from = fields.List(fields.Str, allow_none=True)
    entity_derivations = fields.Dict(keys=fields.Str, values=fields.List(fields.Str))
    count = fields.Integer(allow_none=True)
    min_count = fields.Integer(allow_none=True)
    max_count = fields.Integer(allow_none=True)
    invalidate = fields.Bool(allow_none=True)
    from_reference = fields.Bool()
    for_each = fields.List(fields.Str, allow_none=True)
    from_pool = fields.Nested(FromPoolConfigSchema, allow_none=True)
    revise_stowaway_samples = fields.Bool(allow_none=True)
    comment = fields.Str(allow_none=True)
