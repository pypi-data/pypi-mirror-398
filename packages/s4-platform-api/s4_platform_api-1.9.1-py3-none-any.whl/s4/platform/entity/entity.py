from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from marshmallow import fields as marshmallow_fields, post_load

from s4.platform.connection import Connection
from s4.platform.entity.field_value import FieldValue, FieldValueSchema
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.internal.lazy_property_list import LazyPropertyList
from s4.platform.shared_schemas.iri_list_schema import EntityIriListSchema


class Entity(ConnectedModel, FieldsMixin[FieldValue]):
    derived_from_entities: LazyPropertyList[ConnectedModel, Entity] = LazyPropertyList(
        lambda: EntitySchema(), "derived_from_entity_iris"
    )

    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: str,
        fields: dict[str, FieldValue],
        derived_from_entity_iris: list[str],
        entity_derivations: dict[str, list[str]],
        type_: str,
        invalidated_by: str,
        created_at_time: datetime,
        generated_by_task_iri: str,
        label_field_name: str,
        changeset_iri: Optional[str] = None
    ):
        super().__init__(connection)
        self.iri = iri
        self.fields = fields
        self.derived_from_entity_iris = derived_from_entity_iris
        self.entity_derivations = entity_derivations
        self.type = type_
        self.invalidated_by = invalidated_by
        self.label_field_name = label_field_name
        self.created_at_time = created_at_time
        self.generated_by_task_iri = generated_by_task_iri
        self.changeset_iri = changeset_iri

    @property
    def label(self) -> str:
        if self.label_field_name not in self.fields:
            raise RuntimeError(f"Entity has label_field_name {self.label_field_name} but that field is missing")
        return self.fields[self.label_field_name].value

    @staticmethod
    def get_entity(
            connection: Connection,
            iri: str,
            historical: bool = None,
            before_time: str = None
    ) -> Entity:
        params:Dict[str, str] = dict()
        if historical:
            params["historical"] = "true"
        if before_time is not None:
            params["beforeTime"] = before_time
        json = connection.fetch_json_from_iri(iri, params=params)
        schema = EntitySchema()
        schema.context["connection"] = connection
        return schema.load(json)

    @staticmethod
    def batch_get(
        connection: Connection,
        iris: list[str],
        historical: bool = None,
        before_time:str = None
    ) -> list[Entity]:

        payload = dict({"data": iris,
                        "historical": historical,
                        "before_time": before_time})
        json = connection.post_json(
            "/entity/batchGet", EntityIriListSchema().dump(payload)
        )
        schema = EntityBatchSchema()
        schema.context["connection"] = connection
        return schema.load(json)

    @staticmethod
    def get_current_revisions(
        connection: Connection,
        iris: list[str]
    ) -> dict[str, str]:

        payload = dict({"data": iris})
        return connection.post_json(
            "/entity/revisions/current", EntityIriListSchema().dump(payload)
        )

    @staticmethod
    def get_by_field(
        connection: Connection,
        field_name: str,
        values: list[str],
        include_invalid: bool = None,
        entity_type_iris: list[str] = None,
        exclude_sub_types: bool = None,
    ) -> list[Entity]:

        payload = dict(
            {
                "fieldName": field_name,
                "values": values,
                "includeInvalid": include_invalid,
                "excludeSubtypes": exclude_sub_types,
            }
        )

        return Entity._get_by_(
            connection, payload, "/entity/getByField", entity_type_iris
        )

    @staticmethod
    def get_by_location(
        connection: Connection,
        locations: list[str],
        include_invalid: bool = None,
        entity_type_iris: list[str] = None,
        exclude_sub_types: bool = None,
    ) -> list[Entity]:

        payload = dict(
            {
                "values": locations,
                "includeInvalid": include_invalid,
                "excludeSubtypes": exclude_sub_types,
            }
        )

        return Entity._get_by_(
            connection, payload, "/entity/getByLocation", entity_type_iris
        )

    @staticmethod
    def get_by_label(
        connection: Connection,
        labels: list[str],
        include_invalid: bool = None,
        entity_type_iris: list[str] = None,
        exclude_sub_types: bool = None,
    ) -> list[Entity]:

        payload = dict(
            {
                "values": labels,
                "includeInvalid": include_invalid,
                "excludeSubtypes": exclude_sub_types,
            }
        )

        return Entity._get_by_(
            connection, payload, "/entity/getByLabel", entity_type_iris
        )

    @staticmethod
    def _get_by_(
        connection: Connection,
        payload: dict,
        path: str,
        entity_type_iris: list[str] = None,
    ) -> list[Entity]:

        if entity_type_iris is not None:
            payload["entityTypeIris"] = entity_type_iris

        json = connection.post_json(path, payload)
        schema = EntityBatchSchema()
        schema.context["connection"] = connection
        return schema.load(json)

    def get_content(self, at_task: str = None) -> Dict[str, Entity]:
        params: Dict[str, str] = dict()
        if at_task is not None:
            params["atTask"] = at_task
        json = self.connection.fetch_json_from_iri(self.iri + "/content", params=params)
        schema = EntityContentSchema()
        schema.context["connection"] = self.connection
        return schema.load(json)


class EntitySchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(Entity, **kwargs)

    iri = marshmallow_fields.Str()
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldValueSchema)
    )
    derived_from_entity_iris = marshmallow_fields.List(marshmallow_fields.Str())
    entity_derivations = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str(),
        values=marshmallow_fields.List(marshmallow_fields.Str),
    )
    type = marshmallow_fields.Str(required=True)
    invalidated_by = marshmallow_fields.Str(allow_none=True)
    created_at_time = marshmallow_fields.DateTime()
    generated_by_task_iri = marshmallow_fields.Str(allow_none=True)
    label_field_name = marshmallow_fields.Str(required=True)
    changeset_iri = marshmallow_fields.Str(allow_none=True, required=False)


class EntityBatchSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(list[Entity], **kwargs)

    entities = marshmallow_fields.List(marshmallow_fields.Nested(EntitySchema))

    @post_load
    def make_model(self, data, **kwargs):
        return list(data["entities"])


class EntitySearchResponse(ConnectedModel):
    def __init__(
        self, *, connection: Connection = None, entities: list[Entity], total_count: int
    ):
        super().__init__(connection)
        self.entities = entities
        self.total_count = total_count


class EntitySearchResponseSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(EntitySearchResponse, **kwargs)

    entities = marshmallow_fields.List(marshmallow_fields.Nested(EntitySchema))
    total_count = marshmallow_fields.Int()


class EntityContent(ConnectedModel):
    def __init__(self, *, connection: Connection = None, data: Dict[str, Entity]):
        super().__init__(connection)
        self.data = data


class EntityContentSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(Dict[str, Entity], **kwargs)

    data = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(EntitySchema)
    )

    @post_load
    def make_model(self, data, **kwargs):
        return data["data"]
