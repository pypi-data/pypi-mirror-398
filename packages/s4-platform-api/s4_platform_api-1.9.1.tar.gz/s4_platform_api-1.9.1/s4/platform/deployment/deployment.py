from typing import Optional

from marshmallow import fields
from s4.platform.changeset.changeset import Changeset, ChangesetSchema
from s4.platform.connection import Connection
from s4.platform.environment.environment_configuration import (
    EnvironmentConfiguration,
    EnvironmentConfigurationSchema,
)
from s4.platform.internal.base_model import ConnectedModel
from s4.platform.internal.base_schema import ConnectedModelSchema
from s4.platform.internal.lazy_property import LazyProperty


# Importing EnvironmentSchema at top-level would create a circular dependency
def make_environment_schema():
    from s4.platform.environment.environment import DeployedEnvironmentSchema

    return DeployedEnvironmentSchema()


class Deployment(ConnectedModel):
    environment = LazyProperty[ConnectedModel, "Environment"](
        make_environment_schema, "environment_iri", "/withConfig"
    )
    changeset = LazyProperty[ConnectedModel, Changeset](
        ChangesetSchema, "changeset_iri"
    )

    # No lazy properties for was_generated_by or was_invalidated_by because we don't have Python classes
    # or schemas for these yet.

    def __init__(
        self,
        *,
        connection: Connection = None,
        iri: str,
        environment_iri: str,
        changeset_iri: str,
        was_generated_by: str,
        was_invalidated_by: Optional[str],
        configuration: Optional[EnvironmentConfiguration] = None
    ):
        super().__init__(connection)
        self.iri = iri
        self.environment_iri = environment_iri
        self.changeset_iri = changeset_iri
        self.was_generated_by = was_generated_by
        self.was_invalidated_by = was_invalidated_by
        self.configuration = configuration


class DeploymentSchema(ConnectedModelSchema):
    def __init__(self, **kwargs):
        super().__init__(Deployment, **kwargs)

    iri = fields.Str(load_only=True)
    environment_iri = fields.Str(load_only=True)
    changeset_iri = fields.Str(load_only=True)
    was_generated_by = fields.Str(load_only=True)
    was_invalidated_by = fields.Str(load_only=True, allow_none=True)
    configuration = fields.Nested(
        EnvironmentConfigurationSchema(), load_only=True, allow_none=True
    )
