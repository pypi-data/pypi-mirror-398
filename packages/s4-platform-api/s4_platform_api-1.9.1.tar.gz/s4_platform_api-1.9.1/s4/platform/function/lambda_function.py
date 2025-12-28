from typing import Optional, List

from marshmallow import fields
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema


class LambdaFunction(GraphModel):
    def __init__(
            self,
            *,
            iri: Optional[str],
            path: str,
            output_content_type: str,
            auth_required: Optional[bool] = None,
            crontab: Optional[str],
            name: str,
            environment_variables: Optional[dict],
            image: str,
            memory: Optional[int],
            ephemeral_storage: Optional[int],
            timeout: Optional[int],
            provisioned_concurrency: Optional[int],
            layers: Optional[List[str]],
            secrets: Optional[List[str]]
    ):
        super().__init__(iri)
        self.path = path
        self.output_content_type = output_content_type
        self.auth_required = auth_required
        self.crontab = crontab
        self.name = name
        self.environment_variables = environment_variables
        self.image = image
        self.memory = memory
        self.ephemeral_storage = ephemeral_storage
        self.timeout = timeout
        self.provisioned_concurrency = provisioned_concurrency
        self.layers = layers
        self.secrets = secrets

class LambdaFunctionSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(LambdaFunction, **kwargs)

    iri = fields.Str(load_only=True)
    path = fields.Str()
    output_content_type = fields.Str(allow_none=True)
    auth_required = fields.Boolean(allow_none=True)
    crontab = fields.Str(allow_none=True)
    name = fields.Str()
    environment_variables = fields.Dict(keys=fields.Str(), values=fields.Str(), allow_none=True)
    image = fields.Str()
    memory = fields.Int(allow_none=True)
    ephemeral_storage = fields.Int(allow_none=True)
    timeout = fields.Int(allow_none=True)
    provisioned_concurrency = fields.Int(allow_none=True)
    layers = fields.List(fields.Str(), allow_none=True)
    secrets = fields.List(fields.Str(), allow_none=True)
