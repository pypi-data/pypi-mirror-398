from typing import Optional, TextIO

from marshmallow import EXCLUDE

from s4.platform.changeset.changeset import Changeset, ChangesetSchema
from s4.platform.changeset.deploy_changeset import (
    DeployChangesetSchema,
    DeployChangeset,
)
from s4.platform.claim.claim import Claim, AdHocClaimRequest, AdHocClaimRequestSchema, ClaimSchema
from s4.platform.connection import Connection
from s4.platform.entity.entity import Entity, EntityBatchSchema
from s4.platform.entity.entity import EntitySearchResponseSchema, EntitySearchResponse
from s4.platform.entity_location.entity_location import EntityLocation, EntityLocationSchema
from s4.platform.entity_type.entity_type import (
    EntityType,
    EntityTypeSchema,
    EntityTypeRequestSchema,
)
from s4.platform.environment.environment import Environment, EnvironmentSchema
from s4.platform.environment.environment_configuration import EnvironmentConfiguration
from s4.platform.environment.migration_plan import MigrationPlan
from s4.platform.file.file_reference import FileReference
from s4.platform.function.function import Function, FunctionSchema
from s4.platform.function.lambda_function import LambdaFunction, LambdaFunctionSchema
from s4.platform.link_config.link_config import LinkConfig, LinkConfigSchema
from s4.platform.page_config.page_config import PageConfig, PageConfigSchema
from s4.platform.config.config import Config, ConfigSchema
from s4.platform.storage_view_config.storage_view_config import StorageViewConfig, StorageViewConfigSchema
from s4.platform.page_config.page_container import PageContainer, PageContainerSchema
from s4.platform.prospective_task.prospective_task import ProspectiveTask, ProspectiveTaskSchema
from s4.platform.prospective_task.search import (
    SortDescriptor,
    ProspectiveTaskSummaryPage,
    ProspectiveTaskSearchRequest,
    ProspectiveTaskSearchRequestSchema,
    ProspectiveTaskSummaryPageSchema,
)
from s4.platform.prospective_task_config.field_config import (
    FieldConfig,
    FieldConfigSchema,
)
from s4.platform.prospective_task_config.prospective_task_config import (
    ProspectiveTaskConfig,
    ProspectiveTaskConfigSchema,
)
from s4.platform.queue.queue import Queue
from s4.platform.queue.queue import QueueSchema, QueuedEntitiesRequestSchema
from s4.platform.shared_schemas.field_search_request import (
    FieldSearchRequest,
    FieldSearchRequestSchema,
)
from s4.platform.shared_schemas.iri_list_schema import IriListSchema
from s4.platform.shared_schemas.sort_order import SortOrder, SortOrderSchema
from s4.platform.task.ad_hoc_task import AdHocTaskSchema, AdHocTask
from s4.platform.task.task import Task, TaskSchema
from s4.platform.tenant_config.tenant_config import TenantConfig, TenantConfigSchema
from s4.platform.workflow.workflow import Workflow, WorkflowSchema


class Api(object):
    def __init__(self, connection: Connection):
        self.connection = connection

    #
    # Returns a new API object for the specified environment
    #
    def get_api_for_env(self, environment_name: Optional[str]) -> "Api":
        return Api(self.connection.get_connection_for_env(environment_name))

    #
    # ProspectiveTask
    #
    def start_workflow(self, workflow_iri: str) -> ProspectiveTask:
        return ProspectiveTask.start_workflow(self.connection, workflow_iri)

    def start_workflow_with_input_entities(self, workflow_id: str, entity_iris: list[str]) -> list[ProspectiveTask]:
        schema = ProspectiveTaskSchema(many=True)

        request_body = {
            "data": entity_iris
        }
        result = self.connection.post_json(f"workflow/{workflow_id}/start/toProspectiveTasks", request_body)

        results: list[ProspectiveTask] =  schema.load(result)

        for pt in results:
            pt.connection = self.connection

        return results


    def prospective_task_by_id(self, id_: str) -> ProspectiveTask:
        return ProspectiveTask.by_id(self.connection, id_)

    def prospective_task_create(
        self, workflow_iri: str, activity_id: str, input_entity_iris: list[str]
    ) -> ProspectiveTask:
        return ProspectiveTask.create(
            self.connection, workflow_iri, activity_id, input_entity_iris
        )

    def claimed_prospective_task_by_entities(
        self, input_iri: Optional[str] = None, output_iri: Optional[str] = None
    ) -> Optional[ProspectiveTask]:
        if input_iri is None and output_iri is None:
            raise RuntimeError(
                "claimed_prospective_task_by_entities requires input_iri, output_iri, or both to be "
                "provided"
            )

        return ProspectiveTask.find_claimed_by_entity_iris(
            self.connection, input_iri=input_iri, output_iri=output_iri
        )

    def prospective_task_search(
        self,
        search_term: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        sort_descriptors: Optional[list[SortDescriptor]] = None,
        include_output_entities: Optional[bool] = None,
    ) -> ProspectiveTaskSummaryPage:
        payload = ProspectiveTaskSearchRequest(
            search_term, offset, limit, sort_descriptors, include_output_entities
        )
        payload_schema = ProspectiveTaskSearchRequestSchema()
        json = self.connection.post_json(
            "prospectiveTask/search", payload_schema.dump(payload)
        )

        response_schema = ProspectiveTaskSummaryPageSchema()
        return response_schema.load(json)

    #
    # ProspectiveTaskConfig
    #

    def prospective_task_config_by_id(self, id_: str) -> ProspectiveTaskConfig:
        return ProspectiveTaskConfig.by_id(self.connection, id_)

    def prospective_task_config_create(
        self, config: ProspectiveTaskConfig
    ) -> ProspectiveTaskConfig:
        schema = ProspectiveTaskConfigSchema()
        schema.context["connection"] = self.connection
        json = self.connection.post_json("/prospectiveTaskConfig", schema.dump(config))
        return schema.load(json)

    def prospective_task_config_find(
        self,
        workflow_iri: str = None,
        changeset_iri: str = None,
        activity_id: str = None,
    ) -> Optional[ProspectiveTaskConfig]:
        return ProspectiveTaskConfig.find(
            self.connection, workflow_iri, changeset_iri, activity_id
        )

    #
    # Queue
    #

    def queue_for_activity(
        self, workflow_iri: str, activity_id: str, entity_iris: list[str] = None
    ) -> Queue:
        payload = dict(
            {
                "workflow_iri": workflow_iri,
                "activity_id": activity_id,
                "entity_iris": entity_iris,
            }
        )
        payload_schema = QueuedEntitiesRequestSchema()
        json = self.connection.post_json(
            "/entityLocation/queued", payload_schema.dump(payload)
        )
        schema = QueueSchema()
        schema.context["connection"] = self.connection
        return schema.load(dict({"queuedEntities": json}))

    #
    # Entity
    #

    def batch_get_entities(self, iris: list[str], historical: bool = None, before_time:str = None) -> list[Entity]:
        return Entity.batch_get(self.connection, iris, historical, before_time)

    def batch_get_entity_types(self, iris: list[str]) -> list[EntityType]:
        payload = dict({"data": iris})
        json = self.connection.post_json(
            "/entityType/batchGet", IriListSchema().dump(payload)
        )
        schema = EntityTypeSchema(many=True)
        schema.context["connection"] = self.connection
        return schema.load(json)

    def search_prospective_entities(
        self,
        *,
        entity_type_iris: list[str],
        include_sub_types: bool,
        search_term: str = None,
        search_term_by_fields: dict[str, list[FieldSearchRequest]] = None,
        pattern_fields: dict[str, FieldConfig] = None,
        sort_fields: list[SortOrder] = None,
        is_valid_only: bool = None,
        limit: int = None,
        offset: int = None,
    ) -> EntitySearchResponse:
        search_term_by_fields_payload = None
        if search_term_by_fields is not None:
            search_term_by_fields_payload = dict()
            for k, v in search_term_by_fields.items():
                search_term_by_fields_payload[k] = [
                    FieldSearchRequestSchema().dump(field_term) for field_term in v
                ]

        pattern_fields_payload = None
        if pattern_fields is not None:
            pattern_fields_payload = dict()
            for k, v in pattern_fields.items():
                pattern_fields_payload[k] = FieldConfigSchema().dump(v)

        payload = dict(
            {
                "entityTypeIris": entity_type_iris,
                "includeSubtypes": include_sub_types,
                "searchTerm": search_term,
                "searchTermByFields": search_term_by_fields_payload,
                "patternFields": pattern_fields_payload,
                "sort_fields": SortOrderSchema().dump(sort_fields),
            }
        )

        # limit and offset are only added if the value is not None. The requests lib will otherwise coerce None to 0,
        # which we don't want as the API provides defaults for both params.
        if limit is not None:
            payload["limit"] = limit

        if offset is not None:
            payload["offset"] = offset

        # is_valid_only is only added if the value is not None. The requests lib will otherwise coerce None to false,
        # which we don't want as the API provides a default for the param.
        if is_valid_only is not None:
            payload["isValidOnly"] = is_valid_only

        json = self.connection.post_json("/prospectiveEntity/search", payload)
        schema = EntitySearchResponseSchema()
        schema.context["connection"] = self.connection
        return schema.load(json)

    #
    # Process Definition
    #
    def process_definition_create(self, file: TextIO) -> str:
        response = self.connection.post_files("processDefinition", dict(file=file))
        return response["iri"]

    #
    # Workflow
    #
    def workflow_create(self, workflow: Workflow) -> Workflow:
        schema = WorkflowSchema()
        payload = schema.dump(workflow)
        result = self.connection.post_json("workflow", payload)
        return schema.load(result)


    def get_workflow_by_id(self, workflow_id: str) -> Workflow:
        schema = WorkflowSchema()
        result = self.connection.fetch_json(f"/workflow/{workflow_id}")
        return schema.load(result)


    #
    # Changeset
    #
    def changeset_create(self, changeset: Changeset) -> Changeset:
        schema = ChangesetSchema()
        schema.context["connection"] = self.connection
        payload = schema.dump(changeset)
        result = self.connection.post_json("changeset", payload)
        return schema.load(result)

    #
    # Environment
    #
    def environment_create(self, environment: Environment) -> Environment:
        # The POST /environment endpoint is handled in core-engine, and so has a configurationBlob property
        # instead of a parsed configuration object. This property is always None for a newly created
        # environment, so it's safe to just ignore it.
        schema = EnvironmentSchema(unknown=EXCLUDE)
        schema.context["connection"] = self.connection
        payload = schema.dump(environment)
        result = self.connection.post_json("environment", payload)
        return schema.load(result)

    def environment_deploy(
        self,
        changeset_iri: str,
        short_name: str,
        migration_plan: Optional[MigrationPlan] = None,
        configuration: Optional[EnvironmentConfiguration] = None,
    ) -> Environment:
        request_schema = DeployChangesetSchema()
        payload = request_schema.dump(
            DeployChangeset(
                changeset_iri=changeset_iri,
                configuration=configuration,
                migration_plan=migration_plan,
            )
        )
        result = self.connection.post_json(
            f"environment/{short_name}/deployWithConfig", payload
        )
        response_schema = EnvironmentSchema()
        response_schema.context["connection"] = self.connection
        return response_schema.load(result)

    #
    # File Reference
    #
    def file_reference_create(
        self, filename: str, aws_file_path: Optional[str] = None
    ) -> FileReference:
        return FileReference.new_s3(self.connection, filename, aws_file_path)

    def file_reference_from_iri(self, iri: str) -> FileReference:
        return FileReference.from_iri(self.connection, iri)

    #
    # EntityType
    #
    def create_entity_type(self, entity_type: EntityType) -> EntityType:
        request_schema = EntityTypeRequestSchema()
        request_schema.context["connection"] = self.connection

        payload = request_schema.dump(entity_type)

        response_schema = EntityTypeSchema()
        response_schema.context["connection"] = self.connection
        response = self.connection.post_json("entityType", payload)
        return response_schema.load(response)

    # Functions
    #
    def function_create(self, function: Function) -> Function:
        schema = FunctionSchema()
        payload = schema.dump(function)
        result = self.connection.post_json("function", payload)
        return schema.load(result)

    def lambda_function_create(self, lambda_function: LambdaFunction) -> LambdaFunction:
        schema = LambdaFunctionSchema()
        payload = schema.dump(lambda_function)
        result = self.connection.post_json("function/lambda", payload)
        return schema.load(result)

    #
    # Ad-hoc task
    #
    def commit_ad_hoc_task(self, task: AdHocTask) -> Task:
        payload = AdHocTaskSchema().dump(task)
        result = self.connection.post_json("adHocTask", payload)
        return TaskSchema().load(result)

    def claim_entities_for_ad_hoc_task(self, entity_iris: list[str]) -> Claim:
        claim_request = AdHocClaimRequest(entity_iris=entity_iris)
        payload = AdHocClaimRequestSchema().dump(claim_request)
        result = self.connection.post_json("adHocClaim", payload)
        return ClaimSchema().load(result)

    #
    # Entity Location
    #
    def get_locations_for_entities(self, entity_iris: list[str]) -> list[EntityLocation]:
        result = self.connection.post_json_array("entityLocation", entity_iris)
        return EntityLocationSchema(many=True).load(result)

    #
    # Generic Config
    #
    def post_config(self, config: Config) -> Config:
        schema = ConfigSchema()
        payload = schema.dump(config)
        result = self.connection.post_json("config", payload)
        return schema.load(result)

    def get_config_by_id(self, config_id: str) -> Config:
        schema = ConfigSchema()
        result = self.connection.fetch_json(f"config/{config_id}")
        return schema.load(result)

    def get_configs_for_environment(self, environment_name: str) -> list[Config]:
        schema = ConfigSchema(many=True)
        result = self.connection.fetch_json(f"environment/{environment_name}/configs")
        return schema.load(result)

    #
    # Link Config
    #
    def config_link_create(self, link_config: LinkConfig) -> LinkConfig:
        schema = LinkConfigSchema()
        payload = schema.dump(link_config)
        result = self.connection.post_json("linkConfig", payload)
        return schema.load(result)

    #
    # Page Config
    #
    def post_page_config(self, page_config: PageConfig) -> PageConfig:
        schema = PageConfigSchema()
        payload = schema.dump(page_config)
        result = self.connection.post_json("config/page", payload)
        return schema.load(result)

    def post_page_container(self, page_container: PageContainer) -> PageContainer:
        schema = PageContainerSchema()
        payload = schema.dump(page_container)
        result = self.connection.post_json("config/pageContainer", payload)
        return schema.load(result)


    #
    # Storage View Config
    #
    def post_storage_view_config(self, storage_view_config: StorageViewConfig) -> StorageViewConfig:
        schema = StorageViewConfigSchema()
        payload = schema.dump(storage_view_config)
        result = self.connection.post_json("config/storageView", payload)
        return schema.load(result)

    def get_storage_view_config_by_id(self, storage_view_config_id: str) -> StorageViewConfig:
        schema = StorageViewConfigSchema()
        result = self.connection.fetch_json(f"config/storageView/{storage_view_config_id}")
        return schema.load(result)

    def get_storage_view_config_for_environment(self, environment_name:str) -> StorageViewConfig:
        config_schema = ConfigSchema(many=True)
        params = {
            "configType": "StorageViewConfig"
        }
        configs = self.connection.fetch_json(f"environment/{environment_name}/configs", params)
        configs_loaded: list[Config] = config_schema.load(configs)
        if len(configs_loaded) > 1:
            raise ValueError("environment can only have one storage view config")
        storage_view_config_id = configs_loaded[0].iri.split("/")[-1]
        return self.get_storage_view_config_by_id(storage_view_config_id)

    #
    # Tenant Config
    #
    def post_tenant_config(self, tenant_config: TenantConfig) -> TenantConfig:
        schema = TenantConfigSchema()
        payload = schema.dump(tenant_config)
        result = self.connection.post_json("tenantConfig", payload)
        return schema.load(result)

    def install_tenant_config(self, tenant_config_iri: str):
        self.connection.post_json("tenantConfig/current", tenant_config_iri)

