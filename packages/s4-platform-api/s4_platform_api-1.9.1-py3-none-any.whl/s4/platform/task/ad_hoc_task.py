from typing import Optional

from marshmallow import fields as marshmallow_fields

from s4.platform.entity.ad_hoc_entity import AdHocEntity, AdHocEntitySchema
from s4.platform.entity.field_value import FieldValue, FieldValueSchema
from s4.platform.internal.base_schema import BaseSchema


class AdHocTask(object):
    def __init__(self, *, fields: dict[str, FieldValue], used_entity_iris: list[str],
                 invalidated_entity_iris: list[str],
                 generated_entities: list[AdHocEntity], claim_iri: Optional[str] = None,
                 execution_details_blob: Optional[str] = None):
        self.fields = fields
        self.used_entity_iris = used_entity_iris
        self.invalidated_entity_iris = invalidated_entity_iris
        self.generated_entities = generated_entities
        self.claim_iri = claim_iri
        self.execution_details_blob = execution_details_blob


class AdHocTaskSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(AdHocTask, **kwargs)

    fields = marshmallow_fields.Dict(keys=marshmallow_fields.Str,
                                     values=marshmallow_fields.Nested(FieldValueSchema))
    used_entity_iris = marshmallow_fields.List(marshmallow_fields.Str, dump_only=True)
    invalidated_entity_iris = marshmallow_fields.List(marshmallow_fields.Str, dump_only=True)
    generated_entities = marshmallow_fields.List(marshmallow_fields.Nested(AdHocEntitySchema))
    claim_iri = marshmallow_fields.Str(dump_only=True)
    execution_details_blob = marshmallow_fields.Str(allow_none=True, dump_only=True)
