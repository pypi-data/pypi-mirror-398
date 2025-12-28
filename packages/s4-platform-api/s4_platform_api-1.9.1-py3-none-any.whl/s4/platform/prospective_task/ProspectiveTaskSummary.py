from datetime import datetime
from typing import Optional

from marshmallow import fields as marshmallow_fields

from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task.prospective_field_value import (
    ProspectiveFieldValue,
    ProspectiveFieldValueSchema,
)


class ProspectiveTaskSummary:
    def __init__(
        self,
        *,
        id_: str,
        claim_iri: Optional[str] = None,
        activity_name: str,
        activity_id: str,
        created_at_time: datetime,
        completed_at_time: Optional[datetime] = None,
        started_at_time: Optional[datetime] = None,
        fields: Optional[dict[str, ProspectiveFieldValue]] = None,
        last_changed_at_time: Optional[datetime] = None,
        was_committed_by: Optional[str] = None,
        was_last_changed_by: Optional[str] = None,
        review_requested: Optional[bool] = None,
        num_continuing_outputs: Optional[int] = None,
        was_started_by: Optional[str] = None,
        workflow_iri: str,
        workflow_name: Optional[str] = None,
        environment: Optional[str] = None
    ):
        self.id_ = id_
        self.claim_iri = claim_iri
        self.activity_id = activity_id
        self.activity_name = activity_name
        self.created_at_time = created_at_time
        self.completed_at_time = completed_at_time
        self.started_at_time = started_at_time
        self.fields = fields
        self.last_changed_at_time = last_changed_at_time
        self.was_committed_by = was_committed_by
        self.was_last_changed_by = was_last_changed_by
        self.review_requested = review_requested
        self.num_continuing_outputs = num_continuing_outputs
        self.was_started_by = was_started_by
        self.workflow_iri = workflow_iri
        self.workflow_name = workflow_name
        self.environment = environment


class ProspectiveTaskSummarySchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveTaskSummary, **kwargs)

    id_ = marshmallow_fields.Str(required=True, data_key="id")
    claim_iri = marshmallow_fields.Str(allow_none=True)
    activity_id = marshmallow_fields.Str(required=True)
    activity_name = marshmallow_fields.Str(required=True)
    fields = marshmallow_fields.Dict(
        keys=marshmallow_fields.Str,
        values=marshmallow_fields.Nested(ProspectiveFieldValueSchema()),
    )
    created_at_time = marshmallow_fields.DateTime()
    completed_at_time = marshmallow_fields.DateTime()
    started_at_time = marshmallow_fields.DateTime()
    last_changed_at_time = marshmallow_fields.DateTime(allow_none=True)
    was_committed_by = marshmallow_fields.Str(allow_none=True)
    was_last_changed_by = marshmallow_fields.Str(allow_none=True, load_only=True)
    review_requested = marshmallow_fields.Bool(allow_none=True, load_only=True)
    num_continuing_outputs = marshmallow_fields.Int(allow_none=True, load_only=True)
    was_started_by = marshmallow_fields.Str(allow_none=True, load_only=True)
    workflow_iri = marshmallow_fields.Str(load_only=True)
    workflow_name = marshmallow_fields.Str(allow_none=True, load_only=True)
    environment = marshmallow_fields.Str(allow_none=True, load_only=True)
