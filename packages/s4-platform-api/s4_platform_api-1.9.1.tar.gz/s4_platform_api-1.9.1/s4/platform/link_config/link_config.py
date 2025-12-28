from typing import Optional

from marshmallow import fields

from s4.platform.link_config.new_workbook_link import NewWorkbookLink, NewWorkbookLinkSchema
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema


class LinkConfig(GraphModel):
    def __init__(
        self,
        *,
        iri: Optional[str],
        short_name: str,
        new_workbook: NewWorkbookLink,
    ):
        super().__init__(iri)
        self.short_name = short_name
        self.new_workbook = new_workbook


class LinkConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(LinkConfig, **kwargs)

    iri = fields.Str(allow_none=True)
    short_name = fields.Str()
    new_workbook = fields.Nested(NewWorkbookLinkSchema)
