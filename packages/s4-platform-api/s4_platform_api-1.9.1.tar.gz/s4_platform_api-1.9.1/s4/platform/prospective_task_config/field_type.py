from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class FieldType(Enum):
    BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"
    STRING = "http://www.w3.org/2001/XMLSchema#string"
    DECIMAL = "http://www.w3.org/2001/XMLSchema#decimal"
    INTEGER = "http://www.w3.org/2001/XMLSchema#integer"
    DATE = "http://www.w3.org/2001/XMLSchema#date"
    DATE_TIME = "http://www.w3.org/2001/XMLSchema#dateTime"
    MARKDOWN = "http://www.semaphoresolutions.com/schema/2020/platform#text/markdown"
    FILE_REFERENCE = (
        "http://www.semaphoresolutions.com/schema/2020/platform#FileReference"
    )
    IRI = "http://www.w3.org/2001/XMLSchema#anyURI"
    TYPE_REFERENCE = (
        "http://www.semaphoresolutions.com/schema/2020/platform#TypeReference"
    )
    JSON = (
        "http://www.semaphoresolutions.com/schema/2020/platform#text/json"
    )
    SEQUENCE_TYPE = (
        "http://www.semaphoresolutions.com/schema/2020/platform#Sequence"
    )
    TASK_IRI = "http://www.semaphoresolutions.com/schema/2020/platform#taskIri"
    PRINCIPAL_IRI = "http://www.semaphoresolutions.com/schema/2020/platform#principalIri"

    @staticmethod
    def from_str(value: str) -> Optional["FieldType"]:
        for (name, member) in FieldType.__members__.items():
            if member.value == value:
                return member
        return None

    def value_as_str(self, value: any) -> str:
        if self == FieldType.DATE or self == FieldType.DATE_TIME:
            return value.isoformat()
        return str(value)

    def coerce_from_str(self, value: str):
        if self == FieldType.DECIMAL:
            return Decimal(value)

        if self == FieldType.INTEGER:
            return int(value)

        if self == FieldType.DATE:
            return date.fromisoformat(value)

        if self == FieldType.DATE_TIME:
            return datetime.fromisoformat(value)

        if self == FieldType.BOOLEAN:
            return value.lower() == "true"

        return value
