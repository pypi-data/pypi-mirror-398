class PrePostStage:
    def __init__(self,
            trigger_blocked_info: dict = None
        ) -> None:
        self.trigger_blocked_info = trigger_blocked_info

    def to_dict(self):
        return {
            "triggerBlockedInfo": self.trigger_blocked_info
        }

class PrePostStageConfigMapSecretNames:
    def __init__(self, config_maps : list = None, secrets: list = None):
        self.config_maps = config_maps if config_maps is not None else []
        self.secrets = secrets if secrets is not None else []

    def to_dict(self):
        return {
            "configMaps": self.config_maps,
            "secrets": self.secrets
        }

class StrategyConfig:
    def __init__(self,
            deployment: dict = None
        ) -> None:
        self.deployment = deployment if deployment is not None else {}

    def to_dict(self):
        return {
            "deployment": self.deployment
        }




class Strategy:
    def __init__(self,
            deployment_template : str,
            config              : StrategyConfig,
            default             : bool
        ) -> None:
        self.deployment_template = deployment_template
        self.config = config
        self.default = default

    def to_dict(self):
        return {
            "deploymentTemplate": self.deployment_template,
            "config": self.config.to_dict(),
            "default": self.default
        }


class CdPipeline:
    from tron.core.app.workflow.ci_pipeline.ci_pipeline_models import PrePostBuildConfig

    def __init__(self,
            _id: int = 0,
            environment_id: int = 0,
            environment_name: str = "",
            description: str = "",
            ci_pipeline_id: int = 0,
            trigger_type: str = "MANUAL",
            name: str = "",
            strategies: list = None,
            deployment_template: str = "ROLLING",
            is_cluster_cd_active: bool = False,
            parent_pipeline_id: int = 0,
            parent_pipeline_type: str = "",
            deployment_app_type: str = "",
            app_name: str = "",
            deployment_app_delete_request: bool = False,
            deployment_app_created: bool = False,
            app_id: int = 0,
            is_virtual_environment: bool = False,
            helm_package_name: str = "",
            chart_name: str = "",
            chart_base_version: str = "",
            container_registry_name: str = "",
            repo_name: str = "",
            manifest_storage_type: str = "",
            custom_tag_stage: str = "",
            enable_custom_tag: bool = False,
            is_prod_env: bool = False,
            is_git_ops_repo_not_configured: bool = False,
            switch_from_ci_pipeline_id: int = False,
            add_type: str = "",
            child_pipeline_id: int = 0,
            is_digest_enforced_for_pipeline: bool = False,
            is_digest_enforced_for_env: bool = False,
            application_object_cluster_id: int = 0,
            application_object_namespace: str = "",
            deployment_app_name: str = "",
            release_mode: str = "",
            is_trigger_blocked: bool = False,
            is_custom_chart: bool = False,
            user_approval_config: dict = None,
            custom_tag: dict = None,
            approval_config_data: dict = None,
            trigger_blocked_info: dict = None,
            pre_stage: PrePostStage = None,
            post_stage: PrePostStage = None,
            pre_deploy_stage: PrePostBuildConfig = None,
            post_deploy_stage: PrePostBuildConfig = None,
            pre_stage_config_map_secret_names: PrePostStageConfigMapSecretNames = None,
            post_stage_config_map_secret_names: PrePostStageConfigMapSecretNames = None
            ) -> None:
        self.id = _id
        self.environment_id = environment_id
        self.environment_name = environment_name
        self.description = description
        self.ci_pipeline_id = ci_pipeline_id
        self.trigger_type = trigger_type
        self.name = name
        self.strategies = strategies
        self.deployment_template = deployment_template
        self.pre_stage = pre_stage
        self.post_stage = post_stage
        self.pre_stage_config_map_secret_names = pre_stage_config_map_secret_names
        self.post_stage_config_map_secret_names = post_stage_config_map_secret_names
        self.is_cluster_cd_active = is_cluster_cd_active
        self.parent_pipeline_id = parent_pipeline_id
        self.parent_pipeline_type = parent_pipeline_type
        self.deployment_app_type = deployment_app_type
        self.user_approval_config = user_approval_config
        self.approval_config_data = approval_config_data
        self.app_name = app_name
        self.deployment_app_delete_request = deployment_app_delete_request
        self.deployment_app_created = deployment_app_created
        self.app_id = app_id
        self.is_virtual_environment = is_virtual_environment
        self.helm_package_name = helm_package_name
        self.chart_name = chart_name
        self.chart_base_version = chart_base_version
        self.container_registry_name = container_registry_name
        self.repo_name = repo_name
        self.manifest_storage_type = manifest_storage_type
        self.pre_deploy_stage = pre_deploy_stage
        self.post_deploy_stage = post_deploy_stage
        self.custom_tag = custom_tag
        self.custom_tag_stage = custom_tag_stage
        self.enable_custom_tag = enable_custom_tag
        self.is_prod_env = is_prod_env
        self.is_git_ops_repo_not_configured = is_git_ops_repo_not_configured
        self.switch_from_ci_pipeline_id = switch_from_ci_pipeline_id
        self.add_type = add_type
        self.child_pipeline_id = child_pipeline_id
        self.is_digest_enforced_for_pipeline = is_digest_enforced_for_pipeline
        self.is_digest_enforced_for_env = is_digest_enforced_for_env
        self.application_object_cluster_id = application_object_cluster_id
        self.application_object_namespace = application_object_namespace
        self.deployment_app_name = deployment_app_name
        self.release_mode = release_mode
        self.trigger_blocked_info = trigger_blocked_info
        self.is_trigger_blocked = is_trigger_blocked
        self.is_custom_chart = is_custom_chart
