class CustomTag:

    def __init__(self,
             tag_pattern : str = "",
             counter_x   : int = 0
        ) -> None:

        self.counter_x   = counter_x
        self.tag_pattern = tag_pattern

    def to_dict(self):

        return {
            "counterX": self.counter_x,
            "tagPattern" : self.tag_pattern
        }


class WorkflowCacheConfig:

    def __init__(self,
            global_value : bool = True,
            _type        : str = "INHERIT",
            value        : bool = True

        ) -> None:

        self.type         = _type
        self.value        = value
        self.global_value = global_value

    def to_dict(self):

        return {
            "type"        : self.type,
            "value"       : self.value,
            "globalValue" : self.global_value
        }


class CiMaterialSource:

    def __init__(self,
            _type: str = "",
            value: str = "",
            regex: str = ""

        ) -> None:

        self.type  = _type
        self.value = value
        self.regex = regex

    def to_dict(self):

        return {
            "type"  : self.type,
            "value" : self.value,
            "regex" : self.regex
        }


class CiMaterial:

    def __init__(self,
            git_material_id   : int = 0,
            _id               : int = 0,
            source            : CiMaterialSource = None,
            git_material_name : str = "",
            is_regex          : bool = False
        ) -> None:

        self.git_material_id   = git_material_id
        self.id                = _id
        self.git_material_name = git_material_name
        self.is_regex          = is_regex
        self.source            = source if source is not None else CiMaterialSource()

    def to_dict(self):

        return {
            "gitMaterialId"   : self.git_material_id,
            "id"              : self.id,
            "gitMaterialName" : self.git_material_name,
            "isRegex"         : self.is_regex,
            "source"          : self.source.to_dict()
        }


class ExternalCiConfig:

    def __init__(self):
        pass

    def to_dict(self):
        return {}


class DockerArgs:

    def __init__(self):
        pass

    def to_dict(self):
        return {}


class DockerConfigOverride:

    def __init__(self):
        pass

    def to_dict(self):
        return {}


class InputVariableValueConstraint:

    def __init__(self,
            _id                : int  = 0,
            block_custom_value : bool = False,
            choices            : list = None,
            constraint         : dict = None
        ) -> None:

        self.id                 = _id
        self.block_custom_value = block_custom_value
        self.choices            = choices
        self.constraint         = constraint

    def to_dict(self):

        return {
            "id"               : self.id,
            "blockCustomValue" : self.block_custom_value,
            "choices"          : self.choices,
            "constraint"       : self.constraint,
        }


class InputVariable:

    def __init__(self,
             allow_empty_value : bool = True,
             description       : str = "",
             _format           : str = "STRING",
             _id               : int = 0,
             name              : str = "",
             value             : str = "",
             value_constraint  : InputVariableValueConstraint = None,
             variable_type     : str = "NEW"
         ) -> None:

        self.allow_empty_value  = allow_empty_value
        self.description        = description
        self._format            = _format
        self.id                 = _id
        self.name               = name
        self.value              = value
        self.value_constraint   = value_constraint if value_constraint is not None else InputVariableValueConstraint()
        self.variable_type      = variable_type

    def to_dict(self):

        return {
            "allowEmptyValue"  : self.allow_empty_value,
            "refVariableName"  : "",
            "refVariableStage" : None,
            "valueConstraint"  : self.value_constraint.to_dict(),
            "isRuntimeArg"     : False,
            "defaultValue"     : "",
            "id"               : self.id,
            "value"            : self.value,
            "format"           : self._format,
            "name"             : self.name,
            "description"      : self.description,
            "variableType"     : self.variable_type
        }


class PluginRefStepDetail:

    def __init__(self,
            plugin_id         : int = 0,
            plugin_name       : str = "",
            plugin_version    : str = "",
            input_var_data    : list = None,
            out_put_variables : list = None,
            condition_details : list = None
        ) -> None:

        self.plugin_id         = plugin_id
        self.plugin_name       = plugin_name
        self.plugin_version    = plugin_version
        self.input_variables   = input_var_data if input_var_data is not None else []
        self.output_variables  = out_put_variables if out_put_variables is not None else []
        self.condition_details = condition_details if condition_details is not None else []

    def to_dict(self):

        return {
            "pluginId"         : self.plugin_id,
            "pluginName"       : self.plugin_name,
            "pluginVersion"    : "",
            "inputVariables"   : [input_variable.to_dict() for input_variable in self.input_variables],
            "outputVariables"  : self.output_variables,
            "conditionDetails" : self.condition_details
        }


class PrePostBuildConfigStep:

    def __init__(self,
            _id                          : int = 0,
            name                         : str = "",
            description                  : str = "",
            index                        : int = 0,
            step_type                    : str = "REF_PLUGIN",
            plugin_ref_step_detail       : PluginRefStepDetail = None,
            output_directory_path        : str = None,
            inline_step_detail           : dict = None,
            trigger_if_parent_stage_fail : bool = False
        ) -> None:

        self.id                           = _id
        self.name                         = name
        self.description                  = description
        self.index                        = index
        self.step_type                    = step_type
        self.output_directory_path        = output_directory_path
        self.inline_step_detail           = inline_step_detail
        self.plugin_ref_step_detail       = plugin_ref_step_detail if plugin_ref_step_detail is not None else PluginRefStepDetail()
        self.trigger_if_parent_stage_fail = trigger_if_parent_stage_fail

    def to_dict(self):
        result = {
            "id"                       : self.id,
            "name"                     : self.name,
            "description"              : self.description,
            "index"                    : self.index,
            "stepType"                 : self.step_type,
            "outputDirectoryPath"      : self.output_directory_path,
            "triggerIfParentStageFail" : self.trigger_if_parent_stage_fail
        }
        
        # Add the appropriate detail based on step type
        if self.step_type == "INLINE":
            result["inlineStepDetail"] = self.inline_step_detail if self.inline_step_detail else {}
            result["directoryPath"] = ""
        else:
            result["pluginRefStepDetail"] = self.plugin_ref_step_detail.to_dict()
            result["directoryPath"] = ""
        
        return result


class PrePostBuildConfig:

    def __init__(self,
                 _id                  : int = 0,
                 steps                : list = None,
                 _type                : str = "",
                 trigger_blocked_info : dict = None,
                 name                 : str = "",
                 trigger_type         : str = "MANUAL"
            ) -> None:

        self.type                 = _type
        self.id                   = _id
        self.steps                = steps if steps is not None else []
        self.trigger_blocked_info = trigger_blocked_info
        self.name                 = name
        self.trigger_type         = trigger_type

    def to_dict(self):

        return {
            "name"               : self.name,
            "triggerType"        : self.trigger_type,
            "type"               : self.type,
            "id"                 : self.id,
            "steps"              : [step.to_dict() for step in self.steps],
            "triggerBlockedInfo" : None
        }


class CiPipeline:

    def __init__(self,
            active                     : bool = False,
            enable_custom_tag          : bool = False,
            is_docker_config_overridden : bool = False,
            is_external                : bool = False,
            is_manual                  : bool = False,
            scan_enabled               : bool = False,
            app_id                     : int = 0,
            app_workflow_id            : int = 0,
            _id                        : int = 0,
            last_triggered_env_id      : int = 0,
            linked_count               : int = 0,
            parent_app_id              : int = 0,
            parent_ci_pipeline         : int = 0,
            ci_material                : list = None,
            default_tag                : list = None,
            name                       : str = "",
            pipeline_type              : str = "CI_BUILD",
            custom_tag                 : CustomTag = None,
            docker_args                : DockerArgs = None,
            docker_config_override     : DockerConfigOverride = None,
            external_ci_config         : ExternalCiConfig = None,
            post_build_stage           : PrePostBuildConfig = None,
            pre_build_stage            : PrePostBuildConfig = None,
            workflow_cache_config      : WorkflowCacheConfig = None
        ) -> None:

        self.app_id                      = app_id
        self.app_workflow_id             = app_workflow_id
        self.active                      = active
        self.ci_material                 = ci_material
        self.docker_args                 = docker_args
        self.external_ci_config          = external_ci_config
        self._id                         = _id
        self.is_external                 = is_external
        self.is_manual                   = is_manual
        self.name                        = name
        self.linked_count                = linked_count
        self.scan_enabled                = scan_enabled
        self.pipeline_type               = pipeline_type
        self.custom_tag                  = custom_tag
        self.workflow_cache_config       = workflow_cache_config
        self.pre_build_stage             = pre_build_stage
        self.post_build_stage            = post_build_stage
        self.docker_config_override      = docker_config_override
        self.parent_ci_pipeline          = parent_ci_pipeline
        self.parent_app_id               = parent_app_id
        self.is_docker_config_overridden = is_docker_config_overridden
        self.last_triggered_env_id       = last_triggered_env_id
        self.default_tag                 = default_tag
        self.enable_custom_tag           = enable_custom_tag

    def to_dict(self):
        return {
            "appId": self.app_id,
            "appWorkflowId": self.app_workflow_id,
            "active": self.active,
            "ciMaterial": [m.to_dict() for m in self.ci_material] if self.ci_material else [],
            "dockerArgs": self.docker_args.to_dict() if self.docker_args else None,
            "externalCiConfig": self.external_ci_config.to_dict() if self.external_ci_config else None,
            "id": self._id,
            "isExternal": self.is_external,
            "isManual": self.is_manual,
            "name": self.name,
            "linkedCount": self.linked_count,
            "scanEnabled": self.scan_enabled,
            "pipelineType": self.pipeline_type,
            "customTag": self.custom_tag.to_dict() if self.custom_tag else None,
            "workflowCacheConfig": self.workflow_cache_config.to_dict() if self.workflow_cache_config else None,
            "preBuildStage": self.pre_build_stage.to_dict() if self.pre_build_stage else None,
            "postBuildStage": self.post_build_stage.to_dict() if self.post_build_stage else None,
            "dockerConfigOverride": self.docker_config_override.to_dict() if self.docker_config_override else None,
            "parentCiPipeline": self.parent_ci_pipeline,
            "parentAppId": self.parent_app_id,
            "isDockerConfigOverridden": self.is_docker_config_overridden,
            "lastTriggeredEnvId": self.last_triggered_env_id,
            "defaultTag": self.default_tag if self.default_tag else [],
            "enableCustomTag": self.enable_custom_tag
        }
