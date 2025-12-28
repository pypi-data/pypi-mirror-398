from typing import Optional
from datetime import datetime

from marshmallow import fields

from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema


class TenantConfig(GraphModel):
    def __init__(self, *, iri: Optional[str], configuration_blob: str, created_by: Optional[str], created_at: Optional[datetime]):
        super().__init__(iri)
        self.configuration_blob = configuration_blob
        self.created_by = created_by
        self.created_at = created_at


class TenantConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(TenantConfig, **kwargs)

    iri = fields.Str(allow_none=True)
    configuration_blob = fields.Str(allow_none=True)
    created_by = fields.Str(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
