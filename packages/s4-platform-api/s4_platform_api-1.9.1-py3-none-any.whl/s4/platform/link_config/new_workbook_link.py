from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema


class NewWorkbookLink(object):
    def __init__(
        self,
        *,
        workflow_iri: str,
        activity_id: str,
        path: str,
    ):
        self.workflow_iri = workflow_iri
        self.activity_id = activity_id
        self.path = path


class NewWorkbookLinkSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(NewWorkbookLink, **kwargs)

    workflow_iri = fields.Str()
    activity_id = fields.Str()
    path = fields.Str()
