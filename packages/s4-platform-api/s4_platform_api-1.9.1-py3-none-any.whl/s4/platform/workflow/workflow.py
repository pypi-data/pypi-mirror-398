from typing import Optional

from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema
from s4.platform.workflow.config_mapping import ConfigMapping, ConfigMappingSchema


class Workflow:
    def __init__(
        self,
        *,
        iri: Optional[str],
        process_definition_iri: str,
        config_mappings: list[ConfigMapping],
        workflow_execution_trigger_iris: Optional[list[str]],
        was_derived_from: Optional[str],
        can_start_without_inputs: Optional[bool],
        can_start_with_inputs: Optional[bool] = None,
        start_permission: Optional[str] = None,
        startable_by_public: Optional[bool] = False,
        name: Optional[str] = None
    ):
        self.iri = iri
        self.process_definition_iri = process_definition_iri
        self.workflow_execution_trigger_iris = workflow_execution_trigger_iris
        self.was_derived_from = was_derived_from
        self.config_mappings = config_mappings
        self.can_start_without_inputs = can_start_without_inputs
        self.can_start_with_inputs = can_start_with_inputs
        self.start_permission = start_permission
        self.startable_by_public = startable_by_public
        self.name = name


class WorkflowSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Workflow, **kwargs)

    iri = fields.Str(allow_none=True, load_only=True)
    process_definition_iri = fields.Str()
    workflow_execution_trigger_iris = fields.List(fields.Str(), allow_none=True)
    was_derived_from = fields.Str(allow_none=True)
    can_start_without_inputs = fields.Boolean(allow_none=True)
    can_start_with_inputs = fields.Boolean(allow_none=True)
    config_mappings = fields.List(fields.Nested(ConfigMappingSchema))
    start_permission = fields.Str(allow_none=True, required=False)
    startable_by_public = fields.Bool(allow_none=True)
    name = fields.Str(allow_none=True, required=False)
