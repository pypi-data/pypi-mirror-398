from typing import Optional
from marshmallow import fields
from s4.platform.internal.base_model import GraphModel
from s4.platform.internal.base_schema import BaseSchema

class ActionConfig:
    def __init__(self, workflow_iri: str) -> None:
        self.workflow_iri = workflow_iri
    
class ActionConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(ActionConfig, **kwargs)
    workflow_iri = fields.Str(allow_none=False)

class StorageViewConfig(GraphModel):
    def __init__(
            self,
            *,
            base_type: str,
            iri: Optional[str] = None,
            config_iri: Optional[str] = None,
            check_in_action_config: Optional[ActionConfig] = None,
            check_out_action_config: Optional[ActionConfig] = None,
            move_action_config: Optional[ActionConfig] = None
    ):
        super().__init__(iri)
        self.config_iri = config_iri
        self.base_type = base_type
        self.check_in_action_config = check_in_action_config
        self.check_out_action_config = check_out_action_config
        self.move_action_config = move_action_config

class StorageViewConfigSchema(BaseSchema):
    def __init__(self, **kwargs):
        super().__init__(StorageViewConfig, **kwargs)

    base_type = fields.Str(allow_none=False)
    iri = fields.Str(allow_none=True)
    config_iri = fields.Str(allow_none=True)
    check_in_action_config = fields.Nested(ActionConfigSchema, allow_none=True)
    check_out_action_config = fields.Nested(ActionConfigSchema, allow_none=True)
    move_action_config = fields.Nested(ActionConfigSchema, allow_none=True)


