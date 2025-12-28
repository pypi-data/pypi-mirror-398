from typing import Optional

from marshmallow import fields

from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.page_config.page_container_page_config import PageContainerPageConfigSchema


class PageContainer(GraphModel):
    def __init__(self, *, iri: Optional[str], config_iri: Optional[str], pages: dict):
        super().__init__(iri)
        self.config_iri = config_iri
        self.pages = pages


class PageContainerSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(PageContainer, **kwargs)

    iri = fields.Str(allow_none=True)
    config_iri = fields.Str(allow_none=True)
    pages = fields.Dict(keys=fields.Str, values=fields.Nested(PageContainerPageConfigSchema, allow_none=True))
