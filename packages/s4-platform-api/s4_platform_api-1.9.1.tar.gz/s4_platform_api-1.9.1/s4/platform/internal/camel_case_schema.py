from marshmallow import Schema, EXCLUDE


# Adapted from https://marshmallow.readthedocs.io/en/stable/examples.html#inflection-camel-casing-keys


def camelcase(s):
    parts = s.split("_")
    return parts[0] + "".join(i.title() for i in parts[1:])


class CamelCaseSchema(Schema):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.unknown = EXCLUDE

    """Schema that uses camel-case for its external representation
    and snake-case for its internal representation.
    """

    def on_bind_field(self, field_name, field_obj):
        field_obj.data_key = camelcase(field_obj.data_key or field_name)
