from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from marshmallow import fields as marshmallow_fields
from marshmallow_enum import EnumField
from s4.platform.connection import Connection
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.camel_case_schema import CamelCaseSchema
from s4.platform.internal.fields_mixin import FieldsMixin
from s4.platform.internal.lazy_property import LazyProperty
from s4.platform.prospective_task.function_list import FunctionList, FunctionListSchema
from s4.platform.prospective_task.function_status import (
    FunctionStatusSchema,
    FunctionStatus,
)
from s4.platform.prospective_task.io_group import IoGroup, IoGroupSchema
from s4.platform.prospective_task.prospective_entity import ProspectiveEntity
from s4.platform.prospective_task.prospective_field_value import (
    ProspectiveFieldValue,
    ProspectiveFieldValueSchema,
)
from s4.platform.prospective_task_config.prospective_task_config import (
    ProspectiveTaskConfigSchema,
    ProspectiveTaskConfig,
)
from s4.platform.task.task import TaskRevertResponseSchema, TaskRevertResponse

class ReviewState(Enum):
    NONE = "None"
    REQUESTED = "Requested"
    APPROVED = "Approved"
    PostApprovalFunctionExecution = "PostApprovalFunctionExecution"


class ProspectiveTask(ConnectedModel, FieldsMixin[ProspectiveFieldValue]):
    prospective_task_config = LazyProperty[ConnectedModel, ProspectiveTaskConfig](
        ProspectiveTaskConfigSchema, "prospective_task_config_iri"
    )

    def __init__(
        self,
        *,
        connection: Connection = None,
        id_: str,
        claim_iri: Optional[str],
        task_iri: Optional[str],
        workflow_iri: str,
        changeset_iri: str,
        environment: str,
        prospective_task_config_iri: str,
        activity_id: str,
        activity_name: str,
        fields: dict[str, ProspectiveFieldValue],
        validation_errors: Optional[list[str]] = None,
        io_groups: dict[str, list[IoGroup]],
        created_at_time: datetime,
        completed_at_time: datetime,
        started_at_time: datetime,
        last_changed_at_time: Optional[datetime] = None,
        was_committed_by: Optional[str] = None,
        was_last_changed_by: Optional[str] = None,
        review_state: ReviewState = ReviewState.NONE,
        running_function: Optional[FunctionStatus] = None,
        was_reverted_at_time: Optional[datetime] = None,
        was_reverted_by_user: Optional[str] = None,
        was_started_by: Optional[str] = None,
        workflow_name: Optional[str] = None,
        ui_state: Optional[str] = None,
        num_continuing_outputs: Optional[int] = None,
    ):
        super().__init__(connection)

        self.id_ = id_
        self.claim_iri = claim_iri
        self.task_iri = task_iri
        self.workflow_iri = workflow_iri
        self.changeset_iri = changeset_iri
        self.environment = environment
        self.prospective_task_config_iri = prospective_task_config_iri
        self.activity_id = activity_id
        self.activity_name = activity_name
        self.fields = fields
        self.validation_errors = validation_errors
        self.io_groups = io_groups
        self.created_at_time = created_at_time
        self.completed_at_time = completed_at_time
        self.started_at_time = started_at_time
        self.last_changed_at_time = last_changed_at_time
        self.was_committed_by = was_committed_by
        self.was_last_changed_by = was_last_changed_by
        self.review_state = review_state
        self.running_function = running_function
        self.was_reverted_at_time = was_reverted_at_time
        self.was_reverted_by_user = was_reverted_by_user
        self.was_started_by = was_started_by
        self.workflow_name = workflow_name
        self.ui_state = ui_state
        self.num_continuing_outputs = num_continuing_outputs

    def claim(self) -> ProspectiveTask:
        json = self.connection.post_json(f"prospectiveTask/{self.id_}/claim", None)
        self._update_with_json(json)
        return self

    def commit(self) -> ProspectiveTask:
        json = self.connection.post_json(f"prospectiveTask/{self.id_}/commit", None)
        self._update_with_json(json)
        return self

    def cancel(self):
        self.connection.post_json(f"prospectiveTask/{self.id_}/cancel", None)

    def delete(self):
        self.connection.delete_resource(f"prospectiveTask/{self.id_}")

    def revert(self) -> TaskRevertResponse:
        if not self.task_iri:
            raise AttributeError("Cannot revert an un-committed task")
        task_revert_schema = TaskRevertResponseSchema()
        result = self.connection.post_json(f"task/{self.id_}/revert", json={})
        return task_revert_schema.load(result)

    def save(self) -> ProspectiveTask:
        task_schema = ProspectiveTaskSchema()
        task_schema.context["connection"] = self.connection
        json = task_schema.dump(self)
        result = self.connection.put_json(f"prospectiveTask/{self.id_}", json)
        self._update_with_json(result)
        return self

    def add_inputs(self, input_entity_iris: list[str]) -> ProspectiveTask:
        result = self.connection.post_json(
            f"prospectiveTask/{self.id_}/input", {"data": input_entity_iris}
        )
        self._update_with_json(result)
        return self

    def set_review_state(self, review_state: ReviewState):
        result = self.connection.post_json(
            f"prospectiveTask/{self.id_}/review/{review_state.value}", None
        )
        self._update_with_json(result)
        return self

    def call_platform_function(self, function_name: str) -> ProspectiveTask:
        task_schema = ProspectiveTaskSchema()
        task_schema.context["connection"] = self.connection

        result = self.connection.post_json(
            f"prospectiveTask/{self.id_}/function/{function_name}", {"taskId": self.id_}
        )
        if result is None:
            raise RuntimeError(f"'{function_name}' function returned an empty response")

        self._update_with_json(result)

        if (
            self.running_function is not None
            and self.running_function.result is not None
            and self.running_function.result.status != 200
        ):
            raise RuntimeError(
                f"'{function_name}' function call failed with error: {self.running_function.result.message}"
            )

        return self

    def fetch_platform_functions(self) -> FunctionList:
        result = self.connection.fetch_json(f"prospectiveTask/{self.id_}/function")
        functions_schema = FunctionListSchema()
        return functions_schema.load(result)

    @staticmethod
    def start_workflow(connection: Connection, workflow_iri: str) -> ProspectiveTask:
        payload = dict({"workflow_iri": workflow_iri})

        payload_schema = StartWorkflowSchema()
        json = connection.post_json("accessioningTask", payload_schema.dump(payload))
        return ProspectiveTask._from_json(connection, json)

    @staticmethod
    def by_id(connection: Connection, id_: str) -> ProspectiveTask:
        json = connection.fetch_json(f"prospectiveTask/{id_}")
        return ProspectiveTask._from_json(connection, json)

    @staticmethod
    def find_claimed_by_entity_iris(
        connection: Connection, input_iri: str = None, output_iri: str = None
    ) -> Optional[ProspectiveTask]:
        if input_iri is None and output_iri is None:
            raise RuntimeError(
                "find_claimed_by_entity_iris requires input_iri, output_iri, or both to be provided"
            )

        payload = dict({"input_iri": input_iri, "output_iri": output_iri})

        json = connection.post_json(
            "prospectiveTask/claimed/find", ClaimedTaskFindSchema().dump(payload)
        )
        if not json:
            return None

        return ProspectiveTask._from_json(connection, json)

    @staticmethod
    def create(
        connection: Connection,
        workflow_iri: str,
        activity_id: str,
        input_entity_iris: list[str],
    ) -> ProspectiveTask:
        payload = dict(
            {
                "workflow_iri": workflow_iri,
                "activity_id": activity_id,
                "input_entities": input_entity_iris,
            }
        )
        payload_schema = CreateProspectiveTaskSchema()
        json = connection.post_json("prospectiveTask", payload_schema.dump(payload))
        return ProspectiveTask._from_json(connection, json)

    def inputs_for_group_and_pattern(
        self, group_name: str, pattern_name: str
    ) -> list[ProspectiveEntity]:
        return [
            entity
            for sublist in [
                group[pattern_name]
                for group in [sample.inputs for sample in self.io_groups[group_name]]
            ]
            for entity in sublist
        ]

    def outputs_for_group_and_pattern(
        self, group_name: str, pattern_name: str
    ) -> list[ProspectiveEntity]:
        return [
            entity
            for sublist in [
                group[pattern_name]
                for group in [sample.outputs for sample in self.io_groups[group_name]]
            ]
            for entity in sublist
        ]

    def _update_with_json(self, json: dict) -> None:
        task_schema = ProspectiveTaskSchema()
        task_schema.context["connection"] = self.connection
        new_task_dict = task_schema.load_as_dict(json)

        # Update properties from the deserialized JSON
        for key, value in new_task_dict.items():
            self.__setattr__(key, value)

    @staticmethod
    def _from_json(connection: Connection, json: dict) -> ProspectiveTask:
        task_schema = ProspectiveTaskSchema()
        task_schema.context["connection"] = connection
        return task_schema.load(json)

    def error_summary(self):
        """
        this function searches through the various levels of ioGroups and fields to find validation errors. It explores
        every path until it reaches the leaf node along a particular path. Returns the errors (error_summary) and the
        paths along which those errors occur in list format.
        parameters: n/a
        returns: error_summary
        """
        path = []
        error_summary = []

        self._summarize_leaf(path, self, error_summary)

        for io_group_name, io_group in self.io_groups.items():
            io_group_path = path + [io_group_name]
            for i, group in enumerate(io_group):
                group_path = io_group_path + [str(i)]
                self._summarize_leaf(group_path, group, error_summary)
                self._summarize_group_patterns(
                    group_path + ["inputs"], group.inputs, error_summary
                )
                self._summarize_group_patterns(
                    group_path + ["outputs"], group.outputs, error_summary
                )
        self._summarize_fields(path, self.fields, error_summary)
        return error_summary

    def _summarize_fields(self, path, fields, error_summary):
        for field_name, field in fields.items():
            field_path = path + [field_name]
            self._summarize_leaf(field_path, field, error_summary)

    def _summarize_group_patterns(self, group_path, group_entities, error_summary):
        for pattern_name, entities in group_entities.items():
            pattern_path = group_path + [pattern_name]
            for i, entity in enumerate(entities):
                entity_path = pattern_path + [str(i)]
                self._summarize_leaf(entity_path, entity, error_summary)
                self._summarize_fields(entity_path, entity.fields, error_summary)

    def _summarize_leaf(self, path, obj, err_sum):
        if obj.validation_errors:
            err_sum.append((path, obj.validation_errors))


class ProspectiveTaskSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveTask, **kwargs)

    id_ = marshmallow_fields.Str(required=True, data_key="id")
    claim_iri = marshmallow_fields.Str(allow_none=True)
    task_iri = marshmallow_fields.Str(allow_none=True)
    workflow_iri = marshmallow_fields.Str(required=True)
    changeset_iri = marshmallow_fields.Str(required=True)
    environment = marshmallow_fields.Str(required=True)
    prospective_task_config_iri = marshmallow_fields.Str(required=True)
    activity_id = marshmallow_fields.Str(required=True)
    activity_name = marshmallow_fields.Str(required=True)
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.Nested(ProspectiveFieldValueSchema),
    )
    validation_errors = marshmallow_fields.List(
        marshmallow_fields.Str, load_default=[], load_only=True
    )
    io_groups = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.List(marshmallow_fields.Nested(IoGroupSchema)),
    )
    created_at_time = marshmallow_fields.DateTime(allow_none=True)
    completed_at_time = marshmallow_fields.DateTime(allow_none=True)
    started_at_time = marshmallow_fields.DateTime(allow_none=True)
    last_changed_at_time = marshmallow_fields.DateTime(allow_none=True)
    was_committed_by = marshmallow_fields.Str(allow_none=True)
    was_last_changed_by = marshmallow_fields.Str(allow_none=True, load_only=True)
    review_state = EnumField(ReviewState, by_value=True)
    running_function = marshmallow_fields.Nested(
        FunctionStatusSchema, allow_none=True, load_only=True
    )
    was_reverted_at_time = marshmallow_fields.DateTime(allow_none=True, load_only=True)
    was_reverted_by_user = marshmallow_fields.Str(allow_none=True, load_only=True)
    was_started_by = marshmallow_fields.Str(allow_none=True)
    workflow_name = marshmallow_fields.Str(allow_none=True)
    ui_state = marshmallow_fields.Str(allow_none=True)
    num_continuing_outputs = marshmallow_fields.Integer(allow_none=True)


class CreateProspectiveTaskSchema(CamelCaseSchema):
    workflow_iri = marshmallow_fields.Str(dump_only=True)
    changeset_iri = marshmallow_fields.Str(dump_only=True)
    activity_id = marshmallow_fields.Str(dump_only=True)
    input_entities = marshmallow_fields.List(marshmallow_fields.Str(), dump_only=True)


class ClaimedTaskFindSchema(CamelCaseSchema):
    input_iri = marshmallow_fields.Str(dump_only=True)
    output_iri = marshmallow_fields.Str(dump_only=True)


class StartWorkflowSchema(CamelCaseSchema):
    workflow_iri = marshmallow_fields.Str(dump_only=True)
    changeset_iri = marshmallow_fields.Str(dump_only=True)
