from typing import Optional

from marshmallow import fields

from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema


class PageConfig(GraphModel):
    def __init__(self, *, iri: Optional[str], config_iri: Optional[str], ui_components: list):
        super().__init__(iri)
        self.config_iri = config_iri
        self.ui_components = ui_components


class PageConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(PageConfig, **kwargs)

    iri = fields.Str(allow_none=True)
    config_iri = fields.Str(allow_none=True)
    ui_components = fields.List(fields.Dict, allow_none=True)
