from typing import Optional

from marshmallow import fields
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema


class Function(GraphModel):
    def __init__(
        self,
        *,
        iri: Optional[str],
        path: str,
        output_file: Optional[str],
        output_content_type: Optional[str],
        auth_required: Optional[bool] = None,
        crontab: Optional[str],
        job_spec_template: str
    ):
        super().__init__(iri)
        self.path = path
        self.output_file = output_file
        self.output_content_type = output_content_type
        self.auth_required = auth_required
        self.crontab = crontab
        self.job_spec_template = job_spec_template


class FunctionSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Function, **kwargs)

    iri = fields.Str(load_only=True)
    path = fields.Str()
    output_file = fields.Str(allow_none=True)
    output_content_type = fields.Str(allow_none=True)
    auth_required = fields.Boolean(allow_none=True)
    crontab = fields.Str(allow_none=True)
    job_spec_template = fields.Str(allow_none=True)
