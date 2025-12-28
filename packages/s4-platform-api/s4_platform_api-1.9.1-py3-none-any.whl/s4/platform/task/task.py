from datetime import datetime
from marshmallow import fields as marshmallow_fields
from s4.platform.entity.entity import Entity, EntitySchema
from s4.platform.entity.field_value import FieldValue, FieldValueSchema
from s4.platform.internal.base_schema import BaseSchema
from typing import Optional


class IoGroup(object):
    def __init__(self, id_: Optional[str] = None, label: Optional[str] = None, type_: Optional[str] = None,
                inputs: Optional[dict[str, list[str]]] = None, outputs: Optional[dict[str, list[str]]] = None):
        self.id_ = id_
        self.label = label
        self.type_ = type_
        self.inputs = inputs
        self.outputs = outputs


class IoGroupSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(IoGroup, **kwargs)

    id_ = marshmallow_fields.Str(allow_none=True, data_key="id")
    label = marshmallow_fields.Str(allow_none=True)
    type_ = marshmallow_fields.Str(allow_none=True, data_key="type")
    inputs = marshmallow_fields.Dict(keys=marshmallow_fields.Str(),
                                     values=marshmallow_fields.List(marshmallow_fields.Str()))
    outputs = marshmallow_fields.Dict(keys=marshmallow_fields.Str(),
                                      values=marshmallow_fields.List(marshmallow_fields.Str()))

class TaskRevertResponse(object):
    def __init__(
        self,
        iri: str,
        user_iri: str,
        reverted_task_iri: str,
        invalidated_entity_iris: list[str],
        original_entity_to_replacement: dict[str,str],
        time_stamp: datetime
    ):
        self.iri = iri
        self.user_iri = user_iri
        self.reverted_task_iri = reverted_task_iri
        self.invalidated_entity_iris = invalidated_entity_iris
        self.original_entity_to_replacement = original_entity_to_replacement
        self.time_stamp = time_stamp

class TaskRevertResponseSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(TaskRevertResponse, **kwargs)

    iri = marshmallow_fields.Str(allow_none=False)
    user_iri = marshmallow_fields.Str(allow_none=False)
    reverted_task_iri = marshmallow_fields.Str(allow_none=False)
    invalidated_entity_iris = marshmallow_fields.List(marshmallow_fields.Str, allow_none=False)
    original_entity_to_replacement = marshmallow_fields.Dict(marshmallow_fields.Str, marshmallow_fields.Str, allow_none=False)
    time_stamp = marshmallow_fields.DateTime(allow_none=False)

class Task(object):
    def __init__(self, *, iri: str, claim_iri: Optional[str] = None, fields: dict[str, FieldValue],
                 used_entity_iris: list[str], invalidated_entity_iris: list[str],
                 generated_entities: list[Entity], activity_id: Optional[str] = None, 
                 activity_name: Optional[str] = None, process_definition_iri: Optional[str] = None,
                 execution_details_blob: Optional[str] = None, external_task_output: Optional[str] = None,
                 started_at_time: datetime, ended_at_time: datetime, last_changed_at_time: Optional[datetime] = None,
                 was_committed_by: str, was_last_changed_by: Optional[str] = None,
                 was_reverted_by: Optional[str] = None, workflow_iri: Optional[str] = None,
                 external_task_error_output: Optional[str] = None, changeset_iri: Optional[str] = None,
                 created_at_time: Optional[datetime] = None, reverted_at_time: Optional[datetime] = None,
                 was_started_by: Optional[str] = None, workflow_name: Optional[str] = None,
                 environment: Optional[str] = None, task_config: Optional[str] = None,
                 io_groups: Optional[list[IoGroup]] = None, num_outputs: int):
        self.iri = iri
        self.claim_iri = claim_iri
        self.was_reverted_by = was_reverted_by
        self.was_last_changed_by = was_last_changed_by
        self.was_committed_by = was_committed_by
        self.last_changed_at_time = last_changed_at_time
        self.ended_at_time = ended_at_time
        self.started_at_time = started_at_time
        self.external_task_output = external_task_output
        self.execution_details_blob = execution_details_blob
        self.process_definition_iri = process_definition_iri
        self.activity_name = activity_name
        self.activity_id = activity_id
        self.fields = fields
        self.used_entity_iris = used_entity_iris
        self.invalidated_entity_iris = invalidated_entity_iris
        self.generated_entities = generated_entities
        self.workflow_iri = workflow_iri
        self.external_task_error_output = external_task_error_output
        self.changeset_iri = changeset_iri
        self.created_at_time = created_at_time
        self.reverted_at_time = reverted_at_time
        self.was_started_by = was_started_by
        self.workflow_name = workflow_name
        self.environment = environment
        self.task_config = task_config
        self.io_groups = io_groups
        self.num_outputs = num_outputs


class TaskSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Task, **kwargs)

    iri = marshmallow_fields.Str(load_only=True)
    claim_iri = marshmallow_fields.Str(load_only=True)
    fields = marshmallow_fields.Dict(keys=marshmallow_fields.Str,
                                     values=marshmallow_fields.Nested(FieldValueSchema),
                                     load_only=True)
    used_entity_iris = marshmallow_fields.List(marshmallow_fields.Str, load_only=True)
    invalidated_entity_iris = marshmallow_fields.List(marshmallow_fields.Str, load_only=True)
    generated_entities = marshmallow_fields.List(marshmallow_fields.Nested(EntitySchema))
    was_reverted_by = marshmallow_fields.Str(load_only=True)
    was_last_changed_by = marshmallow_fields.Str(load_only=True)
    was_committed_by = marshmallow_fields.Str(load_only=True)
    last_changed_at_time = marshmallow_fields.DateTime(load_only=True)
    ended_at_time = marshmallow_fields.DateTime(load_only=True)
    started_at_time = marshmallow_fields.DateTime(load_only=True)
    external_task_output = marshmallow_fields.Str(load_only=True)
    execution_details_blob = marshmallow_fields.Str(load_only=True)
    process_definition_iri = marshmallow_fields.Str(load_only=True)
    activity_name = marshmallow_fields.Str(load_only=True)
    activity_id = marshmallow_fields.Str(load_only=True)
    workflow_iri = marshmallow_fields.Str(load_only=True, allow_none=True)
    external_task_error_output = marshmallow_fields.Str(load_only=True, allow_none=True)
    changeset_iri = marshmallow_fields.Str(load_only=True, allow_none=True)
    created_at_time = marshmallow_fields.DateTime(load_only=True, allow_none=True)
    reverted_at_time = marshmallow_fields.DateTime(load_only=True, allow_none=True)
    was_started_by = marshmallow_fields.Str(load_only=True, allow_none=True)
    workflow_name = marshmallow_fields.Str(load_only=True, allow_none=True)
    environment = marshmallow_fields.Str(load_only=True, allow_none=True)
    task_config = marshmallow_fields.Str(load_only=True, allow_none=True)
    io_groups = marshmallow_fields.List(marshmallow_fields.Nested(IoGroupSchema), allow_none=True)
    num_outputs = marshmallow_fields.Int()
