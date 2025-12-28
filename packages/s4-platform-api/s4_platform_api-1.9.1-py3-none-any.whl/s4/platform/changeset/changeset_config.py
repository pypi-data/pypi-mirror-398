from marshmallow import fields, pre_load

from s4.platform.internal.base_schema import BaseSchema
from s4.platform.workflow.workflow import Workflow


class WorkflowWithWorkbookOrder(object):
    def __init__(self, *, workflow_iri: str, workbook_ids: list[str]):
        self.workflow_iri = workflow_iri
        self.workbook_ids = workbook_ids


class ChangesetConfig(object):
    def __init__(self, *, workflow_order: list[WorkflowWithWorkbookOrder]):
        self.workflow_order = workflow_order

    @staticmethod
    def from_workflows(workflows: list[Workflow]):
        # build a default workflow and workbook order based on the order they appear in the workflow and
        # workbook config mappings
        workflow_order = [
            WorkflowWithWorkbookOrder(
                workflow_iri=w.iri,
                workbook_ids=[c.activity_id for c in w.config_mappings],
            )
            for w in workflows
        ]
        return ChangesetConfig(workflow_order=workflow_order)


class WorkflowWithWorkbookOrderSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(WorkflowWithWorkbookOrder, **kwargs)

    workflow_iri = fields.Str()
    workbook_ids = fields.List(fields.Str())


class ChangesetConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ChangesetConfig, **kwargs)

    workflow_order = fields.Nested(WorkflowWithWorkbookOrderSchema, many=True)
