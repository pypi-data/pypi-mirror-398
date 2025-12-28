import enum
from typing import Optional

from marshmallow import fields
from marshmallow_enum import EnumField
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task.ProspectiveTaskSummary import (
    ProspectiveTaskSummary,
    ProspectiveTaskSummarySchema,
)


class SortDirection(enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class SortDescriptor:
    def __init__(self, field: str, direction: SortDirection):
        self.field = field
        self.direction = direction


class FilterDescriptor:
    def __init__(self, users: Optional[list[str]] = None, activity_names: Optional[list[str]] = None,
                 workflow_names: Optional[list[str]] = None):
        self.users = users
        self.activity_names = activity_names
        self.workflow_names = workflow_names


class FilterDescriptorSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FilterDescriptor, **kwargs)

    users = fields.List(fields.Str(), dump_only=True, required=False)
    activity_names = fields.List(fields.Str(), dump_only=True, required=False)
    workflow_names = fields.List(fields.Str(), dump_only=True, required=False)


class ProspectiveTaskSearchRequest:
    def __init__(
        self,
        search_term: str,
        offset: Optional[int],
        limit: Optional[int],
        sort_descriptors: Optional[list[SortDescriptor]],
        include_output_entities: Optional[bool],
        filter_descriptor: Optional[FilterDescriptor] = None
    ):
        self.search_term = search_term
        self.offset = offset
        self.limit = limit
        self.sort_descriptors = sort_descriptors
        self.include_output_entities = include_output_entities
        self.filter_descriptor = filter_descriptor


class ProspectiveTaskSummaryPage:
    def __init__(
        self,
        offset: int,
        total_count: int,
        prospective_tasks: list[ProspectiveTaskSummary],
    ):
        self.offset = offset
        self.total_count = total_count
        self.prospective_tasks = prospective_tasks


class SortDescriptorSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(SortDescriptor, **kwargs)

    field = fields.Str(dump_only=True)
    direction = EnumField(SortDirection, by_value=True, dump_only=True)


class ProspectiveTaskSearchRequestSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveTaskSearchRequest, **kwargs)

    search_term = fields.Str()
    offset = fields.Integer(dump_only=True, allow_none=True)
    limit = fields.Integer(dump_only=True, allow_none=True)
    sort_descriptors = fields.List(
        fields.Nested(SortDescriptorSchema), dump_only=True, allow_none=True
    )
    include_output_entities = fields.Bool(dump_only=True, allow_none=True)
    filter_descriptor = fields.Nested(FilterDescriptorSchema, dump_only=True, allow_none=True)


class ProspectiveTaskSummaryPageSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ProspectiveTaskSummaryPage, **kwargs)

    offset = fields.Integer(load_only=True)
    total_count = fields.Integer(load_only=True)
    prospective_tasks = fields.List(
        fields.Nested(ProspectiveTaskSummarySchema), load_only=True
    )
