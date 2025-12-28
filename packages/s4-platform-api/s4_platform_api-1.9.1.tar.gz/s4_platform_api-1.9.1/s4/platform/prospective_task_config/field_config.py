from typing import Optional

from marshmallow import fields, pre_load, pre_dump
from s4.platform.internal.base_schema import BaseSchema
from s4.platform.prospective_task_config.field_type import FieldType
from s4.platform.prospective_task_config.field_validation import (
    FieldValidation,
    FieldValidationSchema,
)


class FieldConfig(object):
    def __init__(
        self,
        *,
        data_type: str,
        refers_to: str = None,
        required: bool = False,
        value: str = None,
        requires_unique: str = None,
        validation: list[FieldValidation] = None,
        options: list[any] = None,
        scale: Optional[int] = None,
        is_array: bool = False,
        values: list[str] = None,
        expression: str = None,
        comment: str = None
    ):
        self.data_type = data_type
        self.refers_to = refers_to
        self.required = required
        self.value = value
        self.requires_unique = requires_unique
        self.validation = validation
        self.options = options
        self.scale = scale
        self.values = values
        self.expression = expression
        self.is_array = is_array
        self.comment = comment


class FieldPreset(fields.Field):
    def __init__(self, **additional_metadata):
        super().__init__(**additional_metadata)

    def _serialize(self, value, attr, obj, **kwargs):
        field_type = self.get_field_type()
        return None if field_type is None else field_type.value_as_str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        field_type = self.get_field_type()
        return None if field_type is None else field_type.coerce_from_str(value)

    def get_field_type(self) -> Optional[FieldType]:
        data_type = self.context.get("data_type", None)
        field_type = FieldType.from_str(data_type)
        return field_type


class FieldConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(FieldConfig, **kwargs)

    @pre_load
    def copy_type_info_for_load(self, in_data: dict, **kwargs):
        self.context["data_type"] = in_data["dataType"]
        return in_data

    @pre_dump
    def copy_type_info_for_dump(self, data: FieldConfig, many: bool, **kwargs):
        self.context["data_type"] = data.data_type
        return data

    data_type = fields.Str(required=True)
    refers_to = fields.Str(allow_none=True)
    required = fields.Boolean(allow_none=True)
    value = fields.Str(allow_none=True)
    requires_unique = fields.Str(allow_none=True)
    validation = fields.List(fields.Nested(FieldValidationSchema), allow_none=True)
    options = fields.List(FieldPreset(), allow_none=True)
    scale = fields.Int(allow_none=True)
    is_array = fields.Boolean(allow_none=True)
    expression = fields.Str(allow_none=True)
    values = fields.List(fields.Str(), allow_none=True)
    comment = fields.Str(allow_none=True)
