from typing import Optional

from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema


class ConfigMapping:
    def __init__(self, *, iri: Optional[str], activity_id: str, config_iri: str):
        self.iri = iri
        self.activity_id = activity_id
        self.config_iri = config_iri


class ConfigMappingSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ConfigMapping, **kwargs)

    iri = fields.Str(allow_none=True, load_only=True)
    activity_id = fields.Str()
    config_iri = fields.Str()
