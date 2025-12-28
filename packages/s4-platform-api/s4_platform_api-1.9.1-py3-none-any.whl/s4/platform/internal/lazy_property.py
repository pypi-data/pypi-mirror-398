from typing import TypeVar, Callable, Generic, Optional, cast

from marshmallow import Schema
from s4.platform.internal.base_model import ConnectedModel, GraphModel

S = TypeVar("S", bound=ConnectedModel)  # type of host
T = TypeVar("T", bound=GraphModel)  # type of property


# Note that type hinting for descriptors is not working in IntelliJ IDEA or PyCharm
# https://youtrack.jetbrains.com/issue/PY-26184
# https://youtrack.jetbrains.com/issue/PY-44181


class LazyProperty(Generic[S, T]):
    def __init__(
        self, schema_class: Callable[[], Schema], attr: str, args: Optional[str] = None
    ) -> None:
        self._attr = attr
        self._schema_class = schema_class
        self._name = None
        self._args = args

    def __get__(self, instance: S, owner: object) -> T:
        try:
            return getattr(instance, self._name)
        except AttributeError:
            pass

        try:
            iri = getattr(instance, self._attr)
        except AttributeError as error:
            raise RuntimeError(
                f"Host for LazyProperty should have attribute {self._attr}"
            )

        if iri is None:
            return None

        if self._args:
            iri = iri + self._args

        try:
            connection = instance.connection
        except AttributeError as error:
            raise RuntimeError(
                "LazyProperty instances must be attached to objects that have a connection property."
            )

        json = connection.fetch_json_from_absolute_path(iri)

        schema = self._schema_class()
        schema.context["connection"] = connection
        value = schema.load(json)

        setattr(instance, self._name, value)
        return value

    def __set__(self, instance: S, value: T) -> None:
        try:
            iri = value.iri
        except AttributeError:
            raise RuntimeError(
                "Value assigned to LazyProperty must have an iri attribute"
            )

        setattr(instance, self._name, value)
        setattr(instance, self._attr, iri)

    def __set_name__(self, owner, name):
        self._name = "_cached_" + name
