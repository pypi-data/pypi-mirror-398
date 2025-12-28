import enum

from marshmallow_enum import EnumField

from s4.platform.internal.camel_case_schema import CamelCaseSchema


class AccentColor(enum.Enum):
    PRODUCTION = "Production"
    YELLOW = "Yellow"
    TEAL_LIGHT = "TealLight"
    CHROMA = "Chroma"
    GREEN_LIGHT = "GreenLight"
    PURPLE = "Purple"
    VERMILION = "Vermilion"


class EnvironmentCategory(enum.Enum):
    PRODUCTION = "production"
    VALIDATION = "validation"
    DEVELOPMENT = "development"


class EnvironmentConfiguration(object):
    def __init__(self, accent_color: AccentColor):
        self.accent_color = accent_color


class EnvironmentConfigurationSchema(CamelCaseSchema):
    accent_color = EnumField(AccentColor, by_value=True, allow_none=True)
