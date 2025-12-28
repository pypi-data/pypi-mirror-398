from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema


class FieldValidation(object):
    def __init__(
        self,
        *,
        verify: str,
        precondition: str = None,
        error_message: str,
        should_block_claim: bool = None
    ):
        self.verify = verify
        self.precondition = precondition
        self.error_message = error_message
        self.should_block_claim = should_block_claim


class FieldValidationSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FieldValidation, **kwargs)

    verify = fields.Str()
    precondition = fields.Str(allow_none=True)
    error_message = fields.Str()
    should_block_claim = fields.Bool(allow_none=True)
