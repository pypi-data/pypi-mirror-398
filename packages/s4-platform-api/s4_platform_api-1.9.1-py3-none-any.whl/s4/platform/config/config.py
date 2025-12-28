from typing import Optional
from marshmallow import fields
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema

class Config(GraphModel):
    def __init__(
            self,
            iri: Optional[str],
            configuration_type: str,
            configuration_blob: str
    ):
        super().__init__(iri)
        self.configuration_type = configuration_type
        self.configuration_blob = configuration_blob

class ConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Config, **kwargs)
    
    iri = fields.Str(allow_none=True)
    configuration_type = fields.Str(allow_none=False)
    configuration_blob = fields.Str(allow_none=False)
