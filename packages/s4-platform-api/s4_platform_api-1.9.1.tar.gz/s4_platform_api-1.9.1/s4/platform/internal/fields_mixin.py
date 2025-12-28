from typing import TypeVar, Generic, Optional


class BaseFieldValue:
    """
    Base class used as Parent class to correctly type other FieldValue subclasses
    Usage:
        see: class ProspectiveFieldValue(BaseFieldValue)
        see: class ProspectiveFieldValue(BaseFieldValue)
    """

    value: Optional[str]  # only typed property used in FieldsMixin
    data_type: str
    overridden: Optional[bool]


TFieldValue = TypeVar("TFieldValue", bound=BaseFieldValue)


class FieldsMixin(Generic[TFieldValue]):
    """
    Object Mixin w/ getters and setters for a fields attribute
    Usage:
        class ProspectiveEntity(GraphModel, FieldsMixin[ProspectiveFieldValue]):
        def __init__(self, *, iri: Optional[str], fields: dict[str, ProspectiveFieldValue],
                     entity_type: str, validation_errors: Optional[list[str]] = None,
                     created_at_time: Optional[datetime]):
    """

    fields: dict[str, TFieldValue]

    def get(self, key, default=None) -> Optional[str]:
        """
        Returns: the value of field key, if present.
                 Otherwise, arg default if key not in fields or value is None
        """
        try:
            field_value_obj = self.fields[key]
        except KeyError:
            return default

        value = field_value_obj.value
        if value is None:
            return default
        return value

    def __getitem__(self, key) -> str:
        """
        A convenience method to retrieve a 'required' field ie expected to have a value
        Note: The method is implemented to return type: str, despite Generic[TFieldValue].value type: Optional[str]
        Usage:
            object: ProspectiveEntity
            value: str = object[field_key]

        Returns: the value of field key, otherwise
            Raises KeyError if the field is not present
            Raises KeyError if the value is None.

        Point of Information --
                KeyError if the value is None? Why?
                Again, this is a __convenience method__ to retrieve a 'required' field ie
                expected to have a value based on TaskConfig
                If the field is truly 'required' then the configuration should declare it as such.
                If it's optional then it simply won't exist at runtime,
                    hence field_key is None and field_key is 'not present', are treated the same
        """

        field_value_obj = self.fields[key]
        value = field_value_obj.value
        if value is None:
            raise KeyError(f"{key}")
        return value

    def __setitem__(self, key, value) -> None:
        field_value_obj = self.fields[key]
        field_value_obj.value = value
