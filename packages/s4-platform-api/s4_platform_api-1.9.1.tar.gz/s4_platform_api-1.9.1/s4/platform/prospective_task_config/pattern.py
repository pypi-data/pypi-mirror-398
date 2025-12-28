from marshmallow import fields as marshmallow_fields

from typing import Optional, Dict, List
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task_config.copy_forward_config import CopyForwardConfig, CopyForwardConfigSchema
from s4.platform.prospective_task_config.field_config import (
    FieldConfig,
    FieldConfigSchema,
)


class Pattern(object):
    def __init__(
        self,
        *,
        entity_type: Optional[str] = None,
        fields: Dict[str, FieldConfig],
        label_field_name: Optional[str] = None,
        is_outside_entity: bool = False,
        can_be_subtype: bool = False,
        copy_fields_from: Optional[List[CopyForwardConfig]] = None
    ):
        self.entity_type = entity_type
        self.fields = fields
        self.is_outside_entity = is_outside_entity
        self.can_be_subtype = can_be_subtype
        self.label_field_name = label_field_name
        self.copy_fields_from = copy_fields_from


class PatternSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Pattern, **kwargs)

    entity_type = marshmallow_fields.Str(allow_none=True)
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldConfigSchema)
    )
    is_outside_entity = marshmallow_fields.Bool()
    can_be_subtype = marshmallow_fields.Bool()
    label_field_name = marshmallow_fields.Str(allow_none=True)
    copy_fields_from = marshmallow_fields.List(marshmallow_fields.Nested(CopyForwardConfigSchema), allow_none=True)
