from enum import Enum

from marshmallow import fields as marshmallow_fields

from s4.platform.internal.camel_case_schema import CamelCaseSchema


class SignatureConfigRole(Enum):
    editor = "editor"
    reviewer = "reviewer"
    approver = "approver"


class SignatureConfig:
    def __init__(self, reasons: list[str]):
        self.reasons = reasons


class SignatureConfigSchema(CamelCaseSchema):
    reasons = marshmallow_fields.List(marshmallow_fields.Str())
