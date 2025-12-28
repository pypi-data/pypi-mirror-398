from datetime import datetime
from typing import Optional

from marshmallow import fields as marshmallow_fields
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.prospective_task.prospective_field_value import (
    ProspectiveFieldValue,
    ProspectiveFieldValueSchema,
)


class ProspectiveEntity(GraphModel, FieldsMixin[ProspectiveFieldValue]):
    def __init__(
        self,
        *,
        iri: Optional[str],
        fields: dict[str, ProspectiveFieldValue],
        entity_type: str,
        validation_errors: Optional[list[str]] = None,
        created_at_time: Optional[datetime] = None,
        generated_by_task_iri: Optional[str] = None,
        invalidated_by: Optional[str] = None,
        label_field_name: str,
        original_input_iri: Optional[str] = None
    ):
        super().__init__(iri)
        self.fields = fields
        self.entity_type = entity_type
        self.validation_errors = validation_errors
        self.created_at_time = created_at_time
        self.generated_by_task_iri = generated_by_task_iri
        self.invalidated_by = invalidated_by
        self.label_field_name = label_field_name
        self.original_input_iri = original_input_iri


class ProspectiveEntitySchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveEntity, **kwargs)

    iri = marshmallow_fields.Str(allow_none=True)
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.Nested(ProspectiveFieldValueSchema),
    )
    entity_type = marshmallow_fields.Str(required=True)
    validation_errors = marshmallow_fields.List(
        marshmallow_fields.Str(), load_default=[], load_only=True
    )
    created_at_time = marshmallow_fields.DateTime(allow_none=True)
    generated_by_task_iri = marshmallow_fields.Str(allow_none=True)
    invalidated_by = marshmallow_fields.Str(allow_none=True)
    label_field_name = marshmallow_fields.Str(required=True)
    original_input_iri = marshmallow_fields.Str(allow_none=True)
