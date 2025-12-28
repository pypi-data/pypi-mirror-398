from typing import TypeVar, Generic, Callable, Sequence

from marshmallow import Schema
from s4.platform.internal.base_model import ConnectedModel, GraphModel
from s4.platform.internal.lazy_property import LazyProperty

S = TypeVar("S", bound=ConnectedModel)  # type of host
T = TypeVar("T", bound=GraphModel)  # type of property


class _LazyHostList(Sequence[T]):
    def __init__(self, lazy_hosts):
        self.lazy_hosts = lazy_hosts

    def __len__(self) -> int:
        return len(self.lazy_hosts)

    def __getitem__(self, i: int) -> T:
        return self.lazy_hosts[i].lazy_property


# Note that type hinting for descriptors is not working in IntelliJ IDEA or PyCharm
# https://youtrack.jetbrains.com/issue/PY-26184
# https://youtrack.jetbrains.com/issue/PY-44181


class LazyPropertyList(Generic[S, T]):
    def __init__(self, schema_class: Callable[[], Schema], attr: str) -> None:
        self._attr = attr
        self._schema_class = schema_class
        self._name = None
        self.connection = None

    def __get__(self, instance: S, owner: object) -> Sequence[T]:
        class LazyPropertyHost:
            lazy_property: LazyProperty[ConnectedModel, T] = LazyProperty(
                self._schema_class, "iri"
            )

            def __init__(self, api_connection, iri):
                self.connection = api_connection
                self.iri = iri

        try:
            connection = instance.connection
        except AttributeError as error:
            raise RuntimeError(
                "LazyPropertyList instances must be attached to objects that have a connection property."
            )

        try:
            iris = getattr(instance, self._attr)
        except AttributeError as error:
            raise RuntimeError(
                f"Host for LazyPropertyList should have attribute {self._attr}"
            )

        return _LazyHostList([LazyPropertyHost(connection, iri) for iri in iris])

    def __set_name__(self, owner, name):
        self._name = "_cached_" + name
