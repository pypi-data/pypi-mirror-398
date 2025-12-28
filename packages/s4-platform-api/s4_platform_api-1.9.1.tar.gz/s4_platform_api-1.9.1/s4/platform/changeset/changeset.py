from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from marshmallow import fields, post_load, pre_load, pre_dump, EXCLUDE
from s4.platform.changeset.changeset_config import (
    ChangesetConfig,
    ChangesetConfigSchema,
)
from s4.platform.connection import Connection
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.lazy_property import LazyProperty
from s4.platform.internal.lazy_property_list import LazyPropertyList
from s4.platform.workflow.workflow import Workflow, WorkflowSchema


class Changeset(ConnectedModel):
    was_derived_from = LazyProperty[ConnectedModel, "Changeset"](
        lambda: ChangesetSchema(), "was_derived_from_iri"
    )
    workflows: LazyPropertyList[ConnectedModel, Workflow] = LazyPropertyList(
        WorkflowSchema, "workflow_iris"
    )

    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: Optional[str],
        was_derived_from_iri: Optional[str],
        type_iris: Optional[list[str]],
        type_info_iris: Optional[list[str]] = None,
        workflow_iris: list[str],
        function_listener_iris: Optional[list[str]] = None,
        function_iris: Optional[list[str]] = None,
        configuration: Optional[ChangesetConfig] = None,
        attributed_to: Optional[str] = None,
        generated_at: Optional[datetime] = None,
        label: Optional[str] = None,
        links: Optional[list[str]] = None,
        configs: Optional[list[str]] = None,
        sequences: Optional[list[str]] = None

    ):
        super().__init__(connection)
        self.iri = iri
        self.was_derived_from_iri = was_derived_from_iri
        self.type_iris = type_iris
        self.type_info_iris = type_info_iris
        self.workflow_iris = workflow_iris
        self.function_listener_iris = function_listener_iris
        self.function_iris = function_iris
        self.configuration = configuration
        self.attributed_to = attributed_to
        self.generated_at = generated_at
        self.label = label
        self.links = links
        self.configs = configs
        self.sequences = sequences


class ChangesetSchema(ConnectedModelSchema):
    class Meta:
        unknown = EXCLUDE

    def __init__(self, **kwargs):
        super().__init__(Changeset, **kwargs)

    @pre_load
    def load_configuration(self, data, **kwargs):
        if "configurationBlob" in data:
            if data["configurationBlob"] is not None:
                data["configuration"] = json.loads(data["configurationBlob"])
        return data

    @pre_dump
    def dump_configuration_blob(self, data, **kwargs):
        if data.configuration is not None:
            data.configuration_blob = self.declared_fields[
                "configuration"
            ].schema.dumps(data.configuration)
        return data

    iri = fields.Str(allow_none=True)
    was_derived_from_iri = fields.Str(allow_none=True)
    type_iris = fields.List(fields.Str(), allow_none=True)
    type_info_iris = fields.List(fields.Str(), allow_none=True)
    workflow_iris = fields.List(fields.Str())
    function_listener_iris = fields.List(fields.Str(), allow_none=True)
    function_iris = fields.List(fields.Str(), allow_none=True)
    configuration = fields.Nested(
        ChangesetConfigSchema, allow_none=True, load_only=True
    )
    configuration_blob = fields.Str(dump_only=True, required=False)
    attributed_to = fields.Str(load_only=True)
    generated_at = fields.DateTime(load_only=True)
    label = fields.Str(allow_none=True)
    links = fields.List(fields.Str(), allow_none=True)
    configs = fields.List(fields.Str(), allow_none=True)
    sequences = fields.List(fields.Str(), allow_none=True)
