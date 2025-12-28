from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema


class PageContainerPageConfig(object):
    def __init__(self, *, label: str, icon: str, route_label: str, page_config_iri: str):
        self.label = label
        self.icon = icon
        self.route_label = route_label
        self.page_config_iri = page_config_iri


class PageContainerPageConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(PageContainerPageConfig, **kwargs)

    label = fields.Str()
    icon = fields.Str()
    route_label = fields.Str()
    page_config_iri = fields.Str()
