from __future__ import annotations

from datetime import datetime
from typing import Optional

from marshmallow import fields
from marshmallow_enum import EnumField
from s4.platform.changeset.changeset import Changeset, ChangesetSchema
from s4.platform.connection import Connection
from s4.platform.environment.environment_configuration import (
    EnvironmentConfiguration,
    EnvironmentConfigurationSchema, AccentColor, EnvironmentCategory,
)
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.camel_case_schema import CamelCaseSchema
from s4.platform.internal.lazy_property_list import LazyProperty

UNCHANGED = object()


class Environment(ConnectedModel):
    current_changeset: LazyProperty[ConnectedModel, Changeset] = LazyProperty(
        ChangesetSchema, "current_changeset_iri"
    )

    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: Optional[str],
        short_name: str,
        label: Optional[str],
        # @deprecated. This parameter will always be None in objects returned from the Labbit backend and will
        # be ignored by endpoints that expect objects of this type as a payload
        was_generated_by: Optional[str] = None,
        current_changeset_iri: Optional[str] = None,
        configuration: Optional[EnvironmentConfiguration] = None,
        categories: Optional[list[EnvironmentCategory]] = None,
        description: Optional[str] = None,
        accent_color: Optional[AccentColor] = None,
        is_archived: bool = False,
        deployed_at: Optional[datetime] = None,
        deployed_by: Optional[str] = None,
        changeset_label: Optional[str] = None,
        changeset_created_at: Optional[datetime] = None,
        changeset_created_by: Optional[str] = None,
    ):
        super().__init__(connection)
        self.iri = iri
        self.short_name = short_name
        self.label = label if label else short_name
        self.current_changeset_iri = current_changeset_iri
        self.was_generated_by = was_generated_by
        self.configuration = configuration
        self.categories = categories
        self.description = description
        self.accent_color = accent_color
        self.is_archived = is_archived
        self.deployed_at = deployed_at
        self.deployed_by = deployed_by
        self.changeset_label = changeset_label
        self.changeset_created_at = changeset_created_at
        self.changeset_created_by = changeset_created_by



    @staticmethod
    def by_name(connection: Connection, name: str) -> Environment:
        json = connection.fetch_json(f"environment/{name}/withConfig")
        return Environment._from_json(connection, json)

    @staticmethod
    def _from_json(connection: Connection, json: dict) -> Environment:
        task_schema = EnvironmentSchema()
        task_schema.context["connection"] = connection
        return task_schema.load(json)

    @staticmethod
    def create(
            connection: Connection,
            short_name: str,
            label: Optional[str],
            categories: list[EnvironmentCategory] = None,
            description: Optional[str] = None,
            accent_color: Optional[AccentColor] = None,
            is_archived: Optional[bool] = False
    ) -> Environment:
        payload = dict(
            {
                "short_name": short_name,
                "label": label,
                "categories": categories,
                "description": description,
                "accent_color": accent_color,
                "is_archived": is_archived,
            }
        )
        payload_schema = CreateEnvironmentSchema()
        json = connection.post_json("environment", payload_schema.dump(payload))
        return Environment._from_json(connection, json)

    def update(self,
               label: str = UNCHANGED,
               categories: list[EnvironmentCategory] = UNCHANGED,
               description: str = UNCHANGED,
               accent_color: AccentColor = UNCHANGED,
               is_archived: bool = UNCHANGED
               ) -> Environment:
        payload = dict(
            {
                "label": self.label if label == UNCHANGED else label,
                "categories": self.categories if categories == UNCHANGED else categories,
                "description": self.description if description == UNCHANGED else description,
                "accent_color": self.accent_color if accent_color == UNCHANGED else accent_color,
                "is_archived": self.is_archived if is_archived == UNCHANGED else is_archived,
            }
        )
        payload_schema = UpdateEnvironmentSchema()
        json = self.connection.put_json(f"environment/{self.short_name}", payload_schema.dump(payload))
        return Environment._from_json(self.connection, json)


class EnvironmentSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(Environment, **kwargs)

    iri = fields.Str(load_only=True, allow_none=True)
    short_name = fields.Str()
    label = fields.Str()
    was_generated_by = fields.Str(load_only=True, allow_none=True, load_default=None)
    current_changeset_iri = fields.Str(load_only=True, allow_none=True)
    configuration = fields.Nested(EnvironmentConfigurationSchema(), allow_none=True)
    description = fields.Str(allow_none=True)
    categories = fields.List(fields.Enum(EnvironmentCategory, by_value=True, allow_none=True), allow_none=True)
    accent_color = EnumField(AccentColor, by_value=True, allow_none=True)
    is_archived = fields.Bool()
    deployed_at = fields.DateTime(allow_none=True)
    deployed_by = fields.Str(allow_none=True)
    changeset_label = fields.Str(allow_none=True)
    changeset_created_at = fields.DateTime(allow_none=True)
    changeset_created_by = fields.Str(allow_none=True)


class CreateEnvironmentSchema(CamelCaseSchema):
    short_name = fields.Str()
    label = fields.Str()
    description = fields.Str(dump_only=True, allow_none=True)
    categories = fields.List(fields.Enum(EnvironmentCategory, by_value=True, allow_none=True),
                             dump_only=True, allow_none=True)
    accent_color = EnumField(AccentColor, by_value=True, allow_none=True)
    is_archived = fields.Bool(dump_only=True)


class UpdateEnvironmentSchema(CamelCaseSchema):
    label = fields.Str()
    description = fields.Str(dump_only=True, allow_none=True)
    categories = fields.List(fields.Enum(EnvironmentCategory, by_value=True, dump_only=True),
                             dump_only=True, allow_none=True)
    accent_color = EnumField(AccentColor, by_value=True, allow_none=True)
    is_archived = fields.Bool(dump_only=True)
