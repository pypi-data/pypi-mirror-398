from datetime import datetime
from marshmallow import fields
from s4.platform.internal.base_schema import BaseSchema
from typing import Optional


class EntityLocation(object):
    def __init__(self, *, activity_id: str, activity_name: str, entity_iri: str, process_definition_iri: str,
                 changeset_iri: str, claim_iri: Optional[str] = None, queued_at_time: Optional[datetime] = None):
        self.activity_id = activity_id
        self.activity_name = activity_name
        self.entity_iri = entity_iri
        self.process_definition_iri = process_definition_iri
        self.changeset_iri = changeset_iri
        self.claim_iri = claim_iri
        self.queued_at_time = queued_at_time


class EntityLocationSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(EntityLocation, **kwargs)

    activity_id = fields.Str(load_only=True)
    activity_name = fields.Str(load_only=True)
    entity_iri = fields.Str(load_only=True)
    process_definition_iri = fields.Str(load_only=True)
    changeset_iri = fields.Str(load_only=True)
    claim_iri = fields.Str(allow_none=True, load_only=True)
    queued_at_time = fields.Str(allow_none=True, load_only=True)
