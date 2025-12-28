import typing

from marshmallow import post_load
from s4.platform.connection import Connection
from s4.platform.internal.camel_case_schema import CamelCaseSchema


class BaseSchema(CamelCaseSchema):
    def __init__(self, model: type, **kwargs):
        super().__init__(**kwargs)
        self._model = model

    def load_as_dict(
        self,
        data: typing.Union[
            typing.Mapping[str, typing.Any],
            typing.Iterable[typing.Mapping[str, typing.Any]],
        ],
    ) -> dict:
        return self._do_load(data, postprocess=False)

    @post_load
    def make_model(self, data, **kwargs):
        return self._model(**data)


class ConnectedModelSchema(BaseSchema):
    def __init__(self, model: type, **kwargs):
        super().__init__(model, **kwargs)

    @post_load
    def make_model(self, data, **kwargs):
        # "type" is not permitted as a named parameter in constructors. Constructors use "type_", but
        # it's serialized as "type".
        if data.get("type") is not None:
            data["type_"] = data["type"]
            del data["type"]
        connection: Connection = self.context.get("connection", None)
        return self._model(connection=connection, **data)
