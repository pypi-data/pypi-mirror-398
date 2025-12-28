from __future__ import annotations

from marshmallow import fields

from s4.platform.internal.base_schema import BaseSchema
from s4.platform.internal.camel_case_schema import CamelCaseSchema
from s4.platform.queue.entity import QueuedEntitySchema, QueuedEntity


class Queue(object):
    def __init__(self, *, queued_entities: list[QueuedEntity]):
        self.queued_entities = queued_entities


class QueueSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(Queue, **kwargs)

    queued_entities = fields.List(fields.Nested(QueuedEntitySchema))


class QueuedEntitiesRequestSchema(CamelCaseSchema):
    workflow_iri = fields.Str(dump_only=True)
    # @deprecated Removed from the API endpoint 2022-04-26 in changeset 77090abd4b5f76553a6f98d068bf2b3a83c93f7f
    # Values will be ignored by backend
    changeset_iri = fields.Str(dump_only=True)
    activity_id = fields.Str(dump_only=True)
    entity_iris = fields.List(fields.Str, dump_only=True)
    workflow_id = fields.Str(allow_none=True)
