from __future__ import annotations

from typing import Optional, Dict, List

from marshmallow import fields as marshmallow_fields

from s4.platform.connection import Connection
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.camel_case_schema import CamelCaseSchema
from s4.platform.prospective_task_config.field_config import (
    FieldConfig,
    FieldConfigSchema,
)
from s4.platform.prospective_task_config.field_validation import (
    FieldValidation,
    FieldValidationSchema,
)
from s4.platform.prospective_task_config.io_group_config import (
    IoGroupConfig,
    IoGroupConfigSchema,
)
from s4.platform.prospective_task_config.pattern import Pattern, PatternSchema
from s4.platform.prospective_task_config.signature_config import SignatureConfig, SignatureConfigRole, \
    SignatureConfigSchema


class ProspectiveTaskConfig(GraphModel):
    def __init__(
        self,
        *,
        iri: Optional[str],
        task_config_iri: Optional[str],
        group_configs: Dict[str, IoGroupConfig],
        patterns: Dict[str, Pattern],
        fields: Dict[str, FieldConfig],
        validation: List[FieldValidation],
        ui_components: dict,
        functions: List[str],
        transition_functions: Dict[str, List[str]] = None,
        additional_permission: Optional[str],
        requires_review: bool,
        allow_public: Optional[bool] = False,
        record_add_to_draft_time: Optional[bool] = False,
        signature_config: Optional[Dict[SignatureConfigRole, SignatureConfig]] = None
    ):
        super().__init__(iri)
        self.task_config_iri = task_config_iri
        self.group_configs = group_configs
        self.patterns = patterns
        self.fields = fields
        self.validation = validation
        self.ui_components = ui_components
        self.functions = functions
        self.transition_functions = transition_functions
        self.additional_permission = additional_permission
        self.requires_review = requires_review
        self.allow_public = allow_public
        self.record_add_to_draft_time = record_add_to_draft_time
        self.signature_config = signature_config

    @staticmethod
    def by_id(connection: Connection, id_: str) -> ProspectiveTaskConfig:
        json = connection.fetch_json(f"prospectiveTaskConfig/{id_}")
        return ProspectiveTaskConfig._from_json(connection, json)

    @staticmethod
    def find(
        connection,
        workflow_iri: str = None,
        changeset_iri: str = None,
        activity_id: str = None,
    ) -> Optional[ProspectiveTaskConfig]:
        if workflow_iri is None or changeset_iri is None or activity_id is None:
            err = "Finding a prospective task config requires the workflow_iri, changeset_iri, and the activity_id"
            raise RuntimeError(err)

        payload = {
            "workflow_iri": workflow_iri,
            "changeset_iri": changeset_iri,
            "activity_id": activity_id,
        }

        json = connection.post_json(
            "prospectiveTaskConfig/find",
            ProspectiveTaskConfigFindSchema().dump(payload),
        )
        if not json:
            return None

        return ProspectiveTaskConfig._from_json(connection, json)

    @staticmethod
    def _from_json(connection: Connection, json: dict) -> ProspectiveTaskConfig:
        schema = ProspectiveTaskConfigSchema()
        schema.context["connection"] = connection
        return schema.load(json)


class ProspectiveTaskConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveTaskConfig, **kwargs)

    iri = marshmallow_fields.Str()
    task_config_iri = marshmallow_fields.Str(allow_none=True)
    group_configs = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.Nested(IoGroupConfigSchema),
    )
    patterns = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(PatternSchema)
    )
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str, values=marshmallow_fields.Nested(FieldConfigSchema)
    )
    validation = marshmallow_fields.List(
        marshmallow_fields.Nested(FieldValidationSchema)
    )
    ui_components = marshmallow_fields.Dict(allow_none=True)
    functions = marshmallow_fields.List(marshmallow_fields.Str, allow_none=True)
    transition_functions = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.List(marshmallow_fields.Str),
        allow_none=True,
    )
    additional_permission = marshmallow_fields.Str(allow_none=True)
    requires_review = marshmallow_fields.Bool()
    allow_public = marshmallow_fields.Bool()
    record_add_to_draft_time = marshmallow_fields.Bool()
    signature_config = marshmallow_fields.Dict(
        keys=marshmallow_fields.Enum(SignatureConfigRole),
        values=marshmallow_fields.Nested(SignatureConfigSchema),
        allow_none=True
    )


class ProspectiveTaskConfigFindSchema(CamelCaseSchema):
    workflow_iri = marshmallow_fields.Str(dump_only=True)
    changeset_iri = marshmallow_fields.Str(dump_only=True)
    activity_id = marshmallow_fields.Str(dump_only=True)
