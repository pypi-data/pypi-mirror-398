from datetime import datetime
from typing import Optional

from marshmallow import fields as marshmallow_fields

from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.queue.field_value import FieldValue, FieldValueSchema


class Entity(GraphModel, FieldsMixin[FieldValue]):
    def __init__(
        self,
        *,
        iri: str,
        fields: dict[str, FieldValue],
        derived_from_entity_iris: list[str],
        entity_derivations: dict[str, list[str]],
        type_: str,
        invalidated_by: str,
        created_at_time: datetime,
        label_field_name: str,
        generated_by_task_iri: Optional[str] = None,
        changeset_iri: Optional[str] = None
    ):
        super().__init__(iri)
        self.fields = fields
        self.derived_from_entity_iris = derived_from_entity_iris
        self.entity_derivations = entity_derivations
        self.type_ = type_
        self.invalidated_by = invalidated_by
        self.created_at_time = created_at_time
        self.generated_by_task_iri = generated_by_task_iri
        self.label_field_name = label_field_name
        self.changeset_iri = changeset_iri


class QueuedEntity(object):
    def __init__(self, *, entity: Entity, queued_at_time: Optional[datetime]):
        self.entity = entity
        self.queued_at_time = queued_at_time


class QueuedEntitySearchResult(object):
    def __init__(self,
                 *,
                 matching_entities: list[QueuedEntity],
                 entities_in_matching_locations: dict[str, list[QueuedEntity]]):
        self.matching_entities = matching_entities
        self.entities_in_matching_locations = entities_in_matching_locations


class EntitySchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Entity, **kwargs)

    iri = marshmallow_fields.Str()
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldValueSchema)
    )
    derived_from_entity_iris = marshmallow_fields.List(marshmallow_fields.Str)
    entity_derivations = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str(),
        values=marshmallow_fields.List(marshmallow_fields.Str),
    )
    type_ = marshmallow_fields.Str(data_key="type")
    invalidated_by = marshmallow_fields.Str(allow_none=True)
    created_at_time = marshmallow_fields.DateTime()
    generated_by_task_iri = marshmallow_fields.Str(allow_none=True, required=False)
    label_field_name = marshmallow_fields.Str()
    changeset_iri = marshmallow_fields.Str(allow_none=True, required=False)


class QueuedEntitySchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(QueuedEntity, **kwargs)

    entity = marshmallow_fields.Nested(EntitySchema)
    queued_at_time = marshmallow_fields.DateTime()


class QueuedEntitySearchResultSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(QueuedEntitySearchResult, **kwargs)

    matching_entities = marshmallow_fields.List(marshmallow_fields.Nested(QueuedEntitySchema))
    entities_in_matching_locations = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str(),
        values=marshmallow_fields.List(marshmallow_fields.Nested(QueuedEntitySchema)),
    )
