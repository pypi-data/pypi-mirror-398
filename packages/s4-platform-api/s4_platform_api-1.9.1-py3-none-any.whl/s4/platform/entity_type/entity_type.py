from __future__ import annotations

from marshmallow import fields as marshmallow_fields, post_load
from s4.platform.connection import Connection
from s4.platform.entity.field_value import FieldValue, FieldValueSchema
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema, BaseSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.internal.lazy_property_list import LazyPropertyList
from typing import Optional, Dict


class EntityType(ConnectedModel, FieldsMixin):
    # parent_types will include PROV:Entity and one of (s4:Container, s4:Sample, s4:Reagent, etc). These are not
    # retrievable. De-referencing the lazy property will fail with a de-serialization error
    parent_types: LazyPropertyList[ConnectedModel, EntityType] = LazyPropertyList(
        lambda: EntityTypeSchema(), "parent_type_iris"
    )

    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: Optional[str],
        label: str,
        parent_type_iris: list[str] = [],
        direct_parent_type_iris: Optional[list[str]] = None,
        fields: dict[str, FieldValue],
        entity_type_info_iri: Optional[str] = None,
    ):
        super().__init__(connection)
        self.iri = iri
        self.label = label
        self.direct_parent_type_iris = direct_parent_type_iris
        self.parent_type_iris = parent_type_iris
        self.fields = fields
        self.entity_type_info_iri = entity_type_info_iri

    @staticmethod
    def batch_get(
            connection: Connection,
            iris: list[str],
            changeset: Optional[str] = None
    ) -> list[EntityType]:
        payload = dict(
            {
                "data": iris,
                "changesetIri": changeset,
            }
        )

        json_list = connection.post_json("entityType/batchGet", payload)
        schema = EntityTypeSchema()
        schema.context["connection"] = connection
        return [schema.load(json) for json in json_list]


    @staticmethod
    def search(
        connection: Connection, search_params: EntityTypeSearchRequest
    ) -> list[EntityType]:
        payload = EntityTypeSearchRequestSchema().dump(search_params)
        json_list = connection.post_json("entityType/search", payload)
        schema = EntityTypeSchema()
        schema.context["connection"] = connection
        return [schema.load(json) for json in json_list]

    def get_content(self) -> Dict[str, EntityType]:

        json = self.connection.fetch_json_from_absolute_path(self.iri + "/content")
        schema = EntityTypeContentSchema()
        schema.context["connection"] = self.connection
        return schema.load(json)

    @staticmethod
    def get_all(
        connection: Connection, limit: int = 10000, offset: int = 0
    ) -> list[EntityType]:
        json_list = connection.fetch_json(
            "entityType?limit={}&offset={}".format(limit, offset)
        )
        schema = EntityTypeSchema()
        schema.context["connection"] = connection
        return [schema.load(json) for json in json_list]

    @staticmethod
    def create(connection: Connection, type_request: EntityTypeCreateRequest) -> EntityType:
        request_schema = EntityTypeCreateRequestSchema()
        request_schema.context["connection"] = connection

        payload = request_schema.dump(type_request)

        response_schema = EntityTypeSchema()
        response_schema.context["connection"] = connection
        response = connection.post_json("entityType", payload)
        return response_schema.load(response)


class EntityTypeSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(EntityType, **kwargs)

    iri = marshmallow_fields.Str()
    label = marshmallow_fields.Str()
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldValueSchema)
    )
    parent_type_iris = marshmallow_fields.List(marshmallow_fields.Str())
    direct_parent_type_iris = marshmallow_fields.List(marshmallow_fields.Str())
    entity_type_info_iri = marshmallow_fields.Str(allow_none=True)


class EntityTypeCreateRequest(object):
    def __init__(
        self,
        *,
        label: str,
        fields: dict[str, FieldValue],
        iri_local_name: Optional[str] = None,
        parent_type_iris: list[str] = [],
        use_entity_type_infos: Optional[bool] = False,
        direct_parent_type_iris: Optional[list[str]] = None,
    ):
        self.iri_local_name = iri_local_name
        self.label = label
        self.parent_type_iris = parent_type_iris
        self.fields = fields
        self.use_entity_type_infos = use_entity_type_infos,
        self.direct_parent_type_iris = direct_parent_type_iris


class EntityTypeCreateRequestSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(EntityTypeCreateRequest, **kwargs)

    iri_local_name = marshmallow_fields.Str()
    label = marshmallow_fields.Str()
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldValueSchema)
    )
    parent_type_iris = marshmallow_fields.List(marshmallow_fields.Str())
    use_entity_type_infos = marshmallow_fields.Bool()
    direct_parent_type_iris= marshmallow_fields.List(marshmallow_fields.Str(), allow_none=True, required=False)


class EntityTypeRequestSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(EntityType, **kwargs)

    iri = marshmallow_fields.Str()
    label = marshmallow_fields.Str()
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldValueSchema)
    )
    parent_type_iris = marshmallow_fields.List(marshmallow_fields.Str())


class EntityTypeSearchRequest(object):
    def __init__(
        self,
        current_changeset_only: bool,
        ancestor_type_iri: Optional[str] = None,
        label: Optional[str] = None,
    ):
        self.current_changeset_only = current_changeset_only
        self.ancestor_type_iri = ancestor_type_iri
        self.label = label


class EntityTypeSearchRequestSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(EntityType, **kwargs)

    current_changeset_only = marshmallow_fields.Bool(dump_only=True)
    ancestor_type_iri = marshmallow_fields.Str(dump_only=True, allow_none=True)
    label = marshmallow_fields.Str(dump_only=True, allow_none=True)


class EntityTypeContent(ConnectedModel):
    def __init__(self, *, connection: Connection = None, data: Dict[str, EntityType]):
        super().__init__(connection)
        self.data = data


class EntityTypeContentSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(Dict[str, EntityType], **kwargs)

    data = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(EntityTypeSchema)
    )

    @post_load
    def make_model(self, data, **kwargs):
        return data["data"]
