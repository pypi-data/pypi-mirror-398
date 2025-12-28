from typing import Optional

from marshmallow import fields as marshmallow_fields

from s4.platform.connection import Connection
from s4.platform.entity.entity import EntitySchema, Entity
from s4.platform.entity.field_value import FieldValue, FieldValueSchema
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.internal.lazy_property_list import LazyPropertyList


class AdHocEntity(ConnectedModel, FieldsMixin[FieldValue]):
    derived_from_entities: LazyPropertyList[ConnectedModel, Entity] = LazyPropertyList(lambda: EntitySchema(),
                                                                                       'derived_from_entity_iris')

    def __init__(self, *, connection: Connection = None, fields: dict[str, FieldValue],
                 derived_from_entity_iris: list[str], entity_derivations: dict[str, list[str]], type_: str,
                 invalidated_by: Optional[str], label_field_name: str):
        super().__init__(connection)
        self.fields = fields
        self.derived_from_entity_iris = derived_from_entity_iris
        self.entity_derivations = entity_derivations
        self.type = type_
        self.invalidated_by = invalidated_by
        self.label_field_name = label_field_name


class AdHocEntitySchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(AdHocEntity, **kwargs)

    fields = marshmallow_fields.Dict(dump_only=True, keys=marshmallow_fields.Str,
                                     values=marshmallow_fields.Nested(FieldValueSchema))
    derived_from_entity_iris = marshmallow_fields.List(marshmallow_fields.Str(), dump_only=True)
    entity_derivations = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str(),
        values=marshmallow_fields.List(marshmallow_fields.Str),
        dump_only=True
    )
    type = marshmallow_fields.Str(required=True, dump_only=True)
    invalidated_by = marshmallow_fields.Str(allow_none=True, dump_only=True)
    label_field_name = marshmallow_fields.Str(required=True, dump_only=True)
