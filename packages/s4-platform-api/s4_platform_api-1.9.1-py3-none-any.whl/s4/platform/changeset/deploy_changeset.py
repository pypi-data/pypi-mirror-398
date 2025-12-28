from typing import Optional

from marshmallow import fields

from s4.platform.environment.environment_configuration import (
    EnvironmentConfiguration,
    EnvironmentConfigurationSchema,
)
from s4.platform.environment.migration_plan import MigrationPlan, MigrationPlanSchema
from s4.platform.internal.base_schema import BaseSchema


class DeployChangeset(object):
    def __init__(
        self,
        changeset_iri: str,
        migration_plan: Optional[MigrationPlan] = None,
        configuration: Optional[EnvironmentConfiguration] = None,
    ):
        self.changeset_iri = changeset_iri
        self.migration_plan = migration_plan
        self.configuration = configuration


class DeployChangesetSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(DeployChangeset, **kwargs)

    changeset_iri = fields.Str(dump_only=True)
    migration_plan = fields.Nested(MigrationPlanSchema, dump_only=True)
    configuration = fields.Nested(EnvironmentConfigurationSchema, dump_only=True)
