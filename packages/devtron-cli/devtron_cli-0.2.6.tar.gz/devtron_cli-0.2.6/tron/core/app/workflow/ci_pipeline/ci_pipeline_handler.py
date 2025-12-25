from tron.core.app.workflow.ci_pipeline.ci_pipeline_models import *


class CiPipelineHandlers:
    def __init__(self, base_url: str, headers: dict):
        pass

    @staticmethod
    def get_ci_id_using_name(base_url, headers, ci_pipeline_name: str, app_id):
        import requests

        url = f"{base_url}/orchestrator/app/ci-pipeline/{app_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get CI Pipelines"
                }
            pipelines = response.json().get("result", {}).get("ciPipelines", [])
            for pipeline in pipelines:

                if pipeline.get("name", "") == ci_pipeline_name:
                    return {
                        "success": True,
                        "ci_pipeline_id": pipeline.get("id", 0)
                    }
            return {
                "success": False,
                "error": "CI Pipeline not found"
            }

        except Exception as e:
            print("Could not fetch the CI pipeline ID")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_pre_post_step_variable(input_vars: list) -> list[InputVariable]:
        try:
            input_variables = []
            if input_vars:
                for variable in input_vars:

                    value_constraint = InputVariableValueConstraint(
                        _id=variable.get("valueConstraint", {}).get("id", 0),
                        choices=variable.get("valueConstraint", {}).get("choices", []),
                        block_custom_value=variable.get("valueConstraint", {}).get("blockCustomValue", False),
                        constraint=variable.get("valueConstraint", {}).get("constraint", {})
                    )

                    input_variables.append(InputVariable(
                        allow_empty_value=variable.get("allowEmptyValue", False),
                        description=variable.get("description", ""),
                        _format=variable.get("format", "STRING"),
                        _id=variable.get("id", 0),
                        name=variable.get("name", ""),
                        value=variable.get("value", ""),
                        value_constraint=value_constraint,
                        variable_type=variable.get("variableType", "NEW")
                    ))
                return input_variables

        except Exception as e:
            print("get_pre_post_step_variable", "Exception occurred:", e)
            return []


    @staticmethod
    def get_pre_post_ci_cd_step_detail(plugin_ref_detail: dict) -> PluginRefStepDetail:
        try:
            input_vars = plugin_ref_detail.get("inputVariables", [])
            input_variables = CiPipelineHandlers.get_pre_post_step_variable(input_vars)

            return PluginRefStepDetail(
                plugin_id=plugin_ref_detail.get("pluginId", 0),
                plugin_name=plugin_ref_detail.get("pluginName", ""),
                plugin_version=plugin_ref_detail.get("pluginVersion", ""),
                input_var_data=input_variables,
                out_put_variables=plugin_ref_detail.get("outputVariables", []),
                condition_details=plugin_ref_detail.get("conditionDetails", [])
            )

        except Exception as e:
            print("get_pre_post_ci_cd_step_detail","Exception occurred:", e)
            return {}


    @staticmethod
    def get_pre_post_ci_step(step: dict) -> PrePostBuildConfigStep:

        try:
            step_type = step.get("stepType", "REF_PLUGIN")
            
            if step_type == "INLINE":
                # Handle INLINE step
                return PrePostBuildConfigStep(
                    _id=step.get("id", 0),
                    name=step.get("name", ""),
                    description=step.get("description", ""),
                    index=step.get("index", 0),
                    step_type=step_type,
                    plugin_ref_step_detail=PluginRefStepDetail(),
                    output_directory_path=step.get("outputDirectoryPath", []),
                    inline_step_detail=step.get("inlineStepDetail", {}),
                    trigger_if_parent_stage_fail=step.get("triggerIfParentStageFail", False)
                )
            else:
                # Handle REF_PLUGIN step
                plugin_ref_step_detail = CiPipelineHandlers.get_pre_post_ci_cd_step_detail(step.get("pluginRefStepDetail", {}))

                return PrePostBuildConfigStep(
                    _id=step.get("id", 0),
                    name=step.get("name", ""),
                    description=step.get("description", ""),
                    index=step.get("index", 0),
                    step_type=step.get("stepType", ""),
                    output_directory_path=step.get("outputDirectoryPath", None),
                    inline_step_detail=step.get("inlineStepDetail", {}),
                    trigger_if_parent_stage_fail=step.get("triggerIfParentStageFail", False),
                    plugin_ref_step_detail=plugin_ref_step_detail
                )

        except Exception as e:
            print("get_pre_post_ci_step",f"Exception occurred:", e)
            return {}


    @staticmethod
    def get_pre_post_build_config(pre_post_ci_cd_stage: dict) -> PrePostBuildConfig:
        try:
            if not pre_post_ci_cd_stage:
                return {}
            pre_post_ci_steps = []

            for step in pre_post_ci_cd_stage.get("steps", []):
                pre_post_ci_steps.append(CiPipelineHandlers.get_pre_post_ci_step(step))

            return PrePostBuildConfig(
                _type=pre_post_ci_cd_stage.get("type", ""),
                _id=pre_post_ci_cd_stage.get("id", 0),
                trigger_blocked_info=pre_post_ci_cd_stage.get("triggerBlockedInfo", {}),
                steps=pre_post_ci_steps
            )

        except Exception as e:
            print("get_pre_post_build_config","Exception occurred:", e)
            return {}


    @staticmethod
    def check_if_plugin_updated(plugin_name: str = "", plugin_id: int = 0, plugin_version: str = "1.0.0", plugin_metadata: dict = None) -> dict:

        for plugin in plugin_metadata.get("parentPlugins", []):
            for minimal_plugin_version_data in plugin.get("pluginVersions", {}).get("minimalPluginVersionData", []):
                if plugin_name == minimal_plugin_version_data["name"]:

                    if plugin_version == minimal_plugin_version_data["pluginVersion"] and plugin_id == minimal_plugin_version_data["id"]:

                        return {
                            "is_modified": False,
                            "field": {}
                        }
                    elif plugin_version == minimal_plugin_version_data["pluginVersion"]:

                        return {
                            "is_modified": True,
                            "field": {
                                "pluginId" : minimal_plugin_version_data["id"],
                                "pluginVersion": minimal_plugin_version_data["pluginVersion"]
                            }
                        }

        return {
            "is_modified": True,
            "field": {"pluginName": plugin_name }
        }

    @staticmethod
    def update_pre_post_ci_steps(current_steps: list, new_steps: list, plugin_metadata: dict, applied_plugin_metadata: list) -> list:
        import re
        try:
            current_steps_indices = {}
            plugin_minimal_data = {}

            for plugin in plugin_metadata.get("parentPlugins", []):
                for version in plugin.get("pluginVersions", {}).get("detailedPluginVersionData", []):
                    (plugin_name, plugin_version) = (version.get("name", ""), version.get("pluginVersion", ""))

                    if (plugin_name, plugin_version) != ("", ""):
                        plugin_minimal_data[(plugin_name, plugin_version)] = version

            plugin_name = ""
            for i in range(len(current_steps)):
                # Handle both plugin and custom steps
                if current_steps[i].step_type == "REF_PLUGIN":
                    for parentPlugin in plugin_metadata.get("parentPlugins", []):
                        for minimal_plugin_version_data in parentPlugin.get("pluginVersions", {}).get("minimalPluginVersionData", []):
                            if minimal_plugin_version_data.get("id", 0) == current_steps[i].plugin_ref_step_detail.plugin_id:
                                plugin_name = minimal_plugin_version_data.get("name", "")
                    current_steps_indices[(current_steps[i].name, plugin_name, "plugin")] = current_steps[i]
                elif current_steps[i].step_type == "INLINE":
                    current_steps_indices[(current_steps[i].name, "", "custom")] = current_steps[i]

            index = 1
            updated_steps = []
            
            for step in new_steps:
                step_type = step.get("type", "plugin").lower()
                task_name = step.get("task_name", "")
                
                if step_type == "custom":
                    # Handle custom/INLINE steps
                    existing_step = current_steps_indices.get((task_name, "", "custom"))
                    
                    if existing_step:
                        # Update existing custom step
                        patch_result = CiPipelineHandlers.patch_custom_step(existing_step, step, index)
                        if not patch_result["success"]:
                            print(f"patch_custom_step failed: {patch_result.get('error')}")
                            return current_steps
                        updated_steps.append(patch_result.get("desired_step"))
                    else:
                        # Add new custom step
                        add_result = CiPipelineHandlers.add_new_custom_step(step, index)
                        if not add_result["success"]:
                            print(f"add_new_custom_step failed: {add_result.get('error')}")
                            return current_steps
                        updated_steps.append(add_result.get("desired_step"))
                    index += 1
                    
                else:
                    # Handle plugin steps
                    plugin_name = step.get("name", "")
                    existing_step = current_steps_indices.get((task_name, plugin_name, "plugin"))
                    
                    if existing_step:
                        key = (step.get("name", ""), step.get("version", ""))
                        if key not in plugin_minimal_data:
                            print(f"Plugin version data not found for {key}")
                            return current_steps

                        patch_pre_post_ci_step_result = CiPipelineHandlers.patch_pre_post_ci_step(existing_step, step, index, plugin_minimal_data[key])
                        if not patch_pre_post_ci_step_result["success"]:
                            print(f"patch_pre_post_ci_step failed: {patch_pre_post_ci_step_result.get('error')}")
                            return current_steps
                        updated_steps.append(patch_pre_post_ci_step_result.get("desired_step"))
                        index += 1
                    else:
                        detailed_plugin_version_data = []
                        for plugin_data in applied_plugin_metadata:

                            step_name = step.get("name", "")
                            pattern = re.compile(rf"^{re.escape(step_name)}(\s+[vV]\d.*)?$")
                            plugin_name = plugin_data.get("name")
                            if pattern.match(plugin_name):
                                detailed_plugin_version_data = plugin_data.get("pluginVersions", {}).get("detailedPluginVersionData", [])
                                break
                            elif plugin_name == step_name:
                                detailed_plugin_version_data = plugin_data.get("pluginVersions", {}).get("detailedPluginVersionData", [])
                                break
                        if not detailed_plugin_version_data:
                            print(f"detailed_plugin_version_data not found for plugin: {step.get('name')}")
                            return current_steps

                        add_plugin_result = CiPipelineHandlers.add_new_plugin(step, index, applied_plugin_metadata, detailed_plugin_version_data)
                        if not add_plugin_result["success"]:
                            print(f"add_new_plugin failed: {add_plugin_result.get('error')}")
                            return current_steps
                        updated_steps.append(add_plugin_result.get("desired_step"))
                        index += 1

            return updated_steps

        except Exception as e:
            print("Error occurred in update_pre_post_ci_steps:", str(e))
            return current_steps

    @staticmethod
    def add_new_plugin(step: dict, index: int, applied_plugin_metadata: list, detailed_plugin_version_data: list):


        try:
            plugin_version = step.get("version", "1.0.0")
            plugin = {}
            for data in detailed_plugin_version_data:
                if data.get("pluginVersion", "") == plugin_version:
                    plugin = data
                    break

            input_variables = []
            if plugin.get("inputVariables", []):

                for input_variable in plugin.get("inputVariables", []):

                    input_variables.append(InputVariable(
                        allow_empty_value=input_variable.get("allowEmptyValue", False),
                        description=input_variable.get("description", ""),
                        _format=input_variable.get("format", "STRING"),
                        _id=input_variable.get("id", 0),
                        name=input_variable.get("name", ""),
                        value=step.get("input_variables", {}).get(input_variable.get("name", ""), ""),
                        value_constraint=None,
                        variable_type="NEW"
                    ))

            plugin_ref_step_detail = PluginRefStepDetail(
                    plugin_id=plugin.get("id", 0),
                    plugin_name="",
                    plugin_version=plugin.get("pluginVersion", ""),
                    input_var_data=input_variables,
                    out_put_variables=None,
                    condition_details=None
                )

            desired_step = PrePostBuildConfigStep(
                _id=index,
                name=step.get("task_name", ""),
                description=step.get("description", ""),
                index=index,
                step_type="REF_PLUGIN",
                plugin_ref_step_detail=plugin_ref_step_detail,
                output_directory_path=None,
                inline_step_detail={},
                trigger_if_parent_stage_fail=False
            )

            return {
                "success": True,
                "desired_step": desired_step,
                "Message": "Plugin object returned successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def add_new_custom_step(step: dict, index: int):
        """
        Add a new custom/INLINE step.
        
        Args:
            step: Step configuration dict
            index: Step index
            
        Returns:
            Dict with success status and desired_step
        """
        try:
            import random
            from tron.core.app.workflow.workflow_handler import Workflow
            
            task_name = step.get("task_name", "")
            description = step.get("description", "")
            script = step.get("script", "")
            script_type = step.get("script_type", "SHELL" if script else "CONTAINER").upper()
            
            # Stringify script
            if script and not isinstance(script, str):
                script = str(script)
            
            # Build input variables
            input_variables = step.get("input_variables", [])
            input_var_data = []
            for var in input_variables:
                key = var.get("key", "")
                var_type = var.get("type", "STRING").upper()
                value = var.get("value", "")
                var_description = var.get("description", "")
                
                input_var_data.append(InputVariable(
                    allow_empty_value=True,
                    description=var_description,
                    _format=var_type,
                    _id=random.randint(1000000000000, 9999999999999),
                    name=key,
                    value=value,
                    value_constraint=None,
                    variable_type="NEW"
                ))
            
            # Build output variables
            output_variables = step.get("output_variables", [])
            output_var_data = Workflow.create_custom_output_variable_payload(output_variables)
            
            # Build condition details
            condition_details = []
            
            trigger_conditions = step.get("trigger_conditions", [])
            if trigger_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(trigger_conditions, "TRIGGER"))
            
            pass_conditions = step.get("pass_conditions", [])
            if pass_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(pass_conditions, "PASS"))
            
            fail_conditions = step.get("fail_conditions", [])
            if fail_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(fail_conditions, "FAIL"))
            
            # Build output directory paths (expects array)
            output_directory_paths = step.get("output_directory_paths")
            if output_directory_paths and not isinstance(output_directory_paths, list):
                # If provided but not a list, convert to list
                output_directory_paths = [output_directory_paths]
            
            # Build inline step detail
            inline_step_detail = {
                "scriptType": script_type,
                "script": script,
                "conditionDetails": condition_details,
                "inputVariables": [var.to_dict() for var in input_var_data],
                "outputVariables": output_var_data,
                "commandArgsMap": step.get("command_args_map", [{"command": "", "args": []}]),
                "portMap": step.get("port_map", []),
                "mountCodeToContainer": step.get("mount_code_to_container", False),
                "mountDirectoryFromHost": step.get("mount_directory_from_host", False)
            }
            
            desired_step = PrePostBuildConfigStep(
                _id=index,
                name=task_name,
                description=description,
                index=index,
                step_type="INLINE",
                plugin_ref_step_detail=PluginRefStepDetail(),
                output_directory_path=output_directory_paths,
                inline_step_detail=inline_step_detail,
                trigger_if_parent_stage_fail=False
            )
            
            return {
                "success": True,
                "desired_step": desired_step,
                "message": "Custom step object created successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def patch_custom_step(current_step: PrePostBuildConfigStep, desired_step: dict, index: int) -> dict:
        """
        Update an existing custom/INLINE step.
        
        Args:
            current_step: Current step object
            desired_step: Desired step configuration dict
            index: Step index
            
        Returns:
            Dict with success status and desired_step
        """
        try:
            import random
            from tron.core.app.workflow.workflow_handler import Workflow
            
            # Update basic fields
            current_step.index = index
            current_step.description = desired_step.get("description", current_step.description)
            
            script = desired_step.get("script", "")
            container_image = desired_step.get("container_image", "")
            
            # Determine script type - check for container image first
            if container_image:
                script_type = "CONTAINER_IMAGE"
            else:
                script_type = desired_step.get("script_type", "SHELL").upper()
            
            # Stringify script
            if script and not isinstance(script, str):
                script = str(script)
            
            # Build a map of existing input variables by name to preserve IDs
            existing_input_vars = {}
            if current_step.inline_step_detail and current_step.inline_step_detail.get("inputVariables"):
                for existing_var in current_step.inline_step_detail.get("inputVariables", []):
                    var_name = existing_var.get("name", "")
                    if var_name:
                        existing_input_vars[var_name] = existing_var.get("id", 0)
            
            # Update input variables - preserve existing IDs
            input_variables = desired_step.get("input_variables", [])
            input_var_data = []
            for var in input_variables:
                key = var.get("key", "")
                var_type = var.get("type", "STRING").upper()
                value = var.get("value", "")
                var_description = var.get("description", "")
                
                # Use existing ID if variable exists, otherwise generate new ID
                var_id = existing_input_vars.get(key, random.randint(1000000000000, 9999999999999))
                
                input_var_data.append(InputVariable(
                    allow_empty_value=True,
                    description=var_description,
                    _format=var_type,
                    _id=var_id,
                    name=key,
                    value=value,
                    value_constraint=None,
                    variable_type="NEW"
                ))
            
            # Build a map of existing output variables by key to preserve IDs
            existing_output_vars = {}
            if current_step.inline_step_detail and current_step.inline_step_detail.get("outputVariables"):
                for existing_var in current_step.inline_step_detail.get("outputVariables", []):
                    var_key = existing_var.get("key", "")
                    if var_key:
                        existing_output_vars[var_key] = existing_var.get("id", 0)
            
            # Update output variables - preserve existing IDs (only for non-container tasks)
            output_var_data = []
            if script_type != "CONTAINER_IMAGE":
                output_variables = desired_step.get("output_variables", [])
                output_var_data = Workflow.create_custom_output_variable_payload(output_variables, existing_output_vars)
            
            # Build a map of existing conditions by (conditionType, key) to preserve IDs
            existing_conditions = {}
            if current_step.inline_step_detail and current_step.inline_step_detail.get("conditionDetails"):
                for existing_cond in current_step.inline_step_detail.get("conditionDetails", []):
                    cond_type = existing_cond.get("conditionType", "")
                    cond_key = existing_cond.get("conditionOnVariable", "")
                    if cond_type and cond_key:
                        existing_conditions[(cond_type, cond_key)] = existing_cond.get("id", 0)
            
            # Update condition details - preserve existing IDs (only for non-container tasks)
            condition_details = []
            if script_type != "CONTAINER_IMAGE":
                trigger_conditions = desired_step.get("trigger_conditions", [])
                if trigger_conditions:
                    condition_details.extend(Workflow.create_condition_details_payload(trigger_conditions, "TRIGGER", existing_conditions))
                
                pass_conditions = desired_step.get("pass_conditions", [])
                if pass_conditions:
                    condition_details.extend(Workflow.create_condition_details_payload(pass_conditions, "PASS", existing_conditions))
                
                fail_conditions = desired_step.get("fail_conditions", [])
                if fail_conditions:
                    condition_details.extend(Workflow.create_condition_details_payload(fail_conditions, "FAIL", existing_conditions))
            
            # Update output directory paths (expects array)
            output_directory_paths = desired_step.get("output_directory_paths")
            if output_directory_paths and not isinstance(output_directory_paths, list):
                # If provided but not a list, convert to list
                output_directory_paths = [output_directory_paths]
            
            # Build inline step detail based on script type
            if script_type == "CONTAINER_IMAGE":
                # Container image task - different structure
                # Parse command and args
                command_list = desired_step.get("command", [])
                if not isinstance(command_list, list):
                    command_list = [command_list] if command_list else []
                
                args_list = desired_step.get("args", [])
                if not isinstance(args_list, list):
                    args_list = [args_list] if args_list else []
                
                command_args_map = [{"command": cmd, "args": args_list} for cmd in command_list] if command_list else [{"command": "", "args": args_list}]
                
                # Parse port mappings
                port_map = []
                ports_mappings = desired_step.get("ports_mappings", [])
                for port_mapping in ports_mappings:
                    if isinstance(port_mapping, str) and ':' in port_mapping:
                        parts = port_mapping.split(':')
                        if len(parts) == 2:
                            port_map.append({
                                "portOnLocal": int(parts[0]),
                                "portOnContainer": int(parts[1])
                            })
                
                # Parse directory mappings
                mount_path_map = []
                directory_mappings = desired_step.get("directory_mappings", [])
                for dir_mapping in directory_mappings:
                    if isinstance(dir_mapping, str) and ':' in dir_mapping:
                        parts = dir_mapping.split(':')
                        if len(parts) == 2:
                            mount_path_map.append({
                                "filePathOnDisk": parts[0],
                                "filePathOnContainer": parts[1]
                            })
                
                # Build container-specific inline_step_detail
                current_step.inline_step_detail = {
                    "scriptType": script_type,
                    "script": script,
                    "inputVariables": [var.to_dict() for var in input_var_data],
                    "containerImagePath": container_image,
                    "isMountCustomScript": bool(script),
                    "commandArgsMap": command_args_map,
                    "portMap": port_map,
                    "mountPathMap": mount_path_map
                }
                
                # Add optional container fields
                if script:
                    current_step.inline_step_detail["storeScriptAt"] = desired_step.get("script_mount_path", "")
                
                script_mount_path_on_container = desired_step.get("script_mount_path_on_container", "")
                if script_mount_path_on_container:
                    current_step.inline_step_detail["mountCodeToContainer"] = True
                    current_step.inline_step_detail["mountCodeToContainerPath"] = script_mount_path_on_container
                
                if mount_path_map:
                    current_step.inline_step_detail["mountDirectoryFromHost"] = True
            else:
                # Regular shell task
                current_step.inline_step_detail = {
                    "scriptType": script_type,
                    "script": script,
                    "conditionDetails": condition_details,
                    "inputVariables": [var.to_dict() for var in input_var_data],
                    "outputVariables": output_var_data,
                    "commandArgsMap": [{"command": "", "args": []}],
                    "portMap": [],
                    "mountCodeToContainer": False,
                    "mountDirectoryFromHost": False
                }
            
            current_step.output_directory_paths = output_directory_paths
            
            return {
                "success": True,
                "desired_step": current_step,
                "message": "Custom step patched successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


    @staticmethod
    def patch_pre_post_ci_step(current_step: PrePostBuildConfigStep, desired_step: dict, index: int, plugin: dict)-> dict:
        try:

            input_variables = []

            for variable in current_step.plugin_ref_step_detail.input_variables:


                tmp = InputVariable(
                    allow_empty_value=variable.allow_empty_value,
                    description=variable.description,
                    _format=variable._format,
                    _id=variable.id,
                    name=variable.name,
                    value=desired_step.get("input_variables", {}).get(variable.name),
                    value_constraint=variable.value_constraint,
                    variable_type=variable.variable_type
                )
                input_variables.append(tmp)

            current_step.index = index
            current_step.plugin_ref_step_detail.plugin_id = plugin.get("id", 0)
            current_step.plugin_ref_step_detail.plugin_version = desired_step.get("version", "")
            current_step.plugin_ref_step_detail.input_variables = input_variables


            return {
                "success": True,
                'desired_step': current_step,
                "message": "Configstep patched"
            }

        except Exception as e:
            print("patch_pre_post_ci_step","Exception occurred:", e)
            return {
                "success": False,
                "error": str(e)
            }


    @staticmethod
    def update_pre_post_ci_steps_old(current_steps: list, new_steps: list, plugin_metadata: dict) -> list:
        index = 1
        for i in range(len(new_steps)):
            for j in range(len(current_steps)):
                if new_steps[i].get("task_name", "") == current_steps[j].name:
                    is_plugin_updated = CiPipelineHandlers.check_if_plugin_updated(new_steps[i].get("name", ""), current_steps[j].pluginRefStepDetail.pluginId, new_steps[i].get("version", ""), plugin_metadata)
                    if not is_plugin_updated["is_modified"]:
                        for variable in current_steps[j].pluginRefStepDetail.inputVariables:
                            variable.value = new_steps[i].get("input_variables", {}).get(variable.name, "")
                        current_steps[j].index = index
                        index += 1
                    else:
                        if is_plugin_updated.get("field", {}).get("pluginVersion", ""):
                            print("Version of the plugin is updated")
                        else:
                            print("Another plugin is getting used")
        return current_steps



    @staticmethod
    def update_pre_post_build_config(current_pre_post_build: PrePostBuildConfig, pre_post_build_config: list, plugin_metadata: dict, applied_plugin_metadata: list, is_cd: bool = False, step_type: str = "", trigger_type: str = "MANUAL") -> PrePostBuildConfig:


        try:

            if not current_pre_post_build:
                current_pre_post_build =  PrePostBuildConfig(
                    steps=[],
                    _type=step_type,
                    trigger_type=trigger_type
                )

            if is_cd:
                current_pre_post_build.trigger_type  = trigger_type

            current_pre_post_build.steps = CiPipelineHandlers.update_pre_post_ci_steps(
                current_pre_post_build.steps,
                pre_post_build_config,
                plugin_metadata,
                applied_plugin_metadata
            )


            return current_pre_post_build

        except Exception as e:
            print("update_pre_post_build_config","Exception occurred:", e)
            return {}


    @staticmethod
    def get_ci_material(ci_material: list[dict]) -> list[CiMaterial]:
        try:
            materials = []
            for material in ci_material:
                source = material.get("source", {})
                ci_material_source = CiMaterialSource(
                    _type=source.get("type", ""),
                    value=source.get("value", ""),
                    regex=source.get("regex", "")
                )
                materials.append(CiMaterial(
                    git_material_id=material.get("gitMaterialId", 0),
                    _id=material.get("id", 0),
                    git_material_name=material.get("gitMaterialName", ""),
                    is_regex=material.get("isRegex", False),
                    source=ci_material_source
                ))
            return materials

        except Exception as e:
            print("get_ci_material","Exception occurred:", e)
            return []


    @staticmethod
    def update_ci_material(ci_material: list[CiMaterial], branches: list[dict]) -> list[CiMaterial]:
        try:

            for i in range(len(branches)):
                ci_material[i].source.type = branches[i].get("type", ci_material[i].source.type)
                ci_material[i].source.value = branches[i].get("branch", ci_material[i].source.value)
                ci_material[i].source.regex = branches[i].get("regex", ci_material[i].source.regex)

            return ci_material

        except Exception as e:
            print("update_ci_material","Exception occurred:", e)
            return []


    @staticmethod
    def get_ci_pipeline(base_url: str, headers: dict, app_id: int, ci_pipeline_id: int) -> dict:
        import requests

        url = f"{base_url}/orchestrator/app/ci-pipeline/{app_id}/{ci_pipeline_id}"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to fetch CI pipeline details: {response.text}"
                }

            details = response.json().get("result", {})

            if details.get("workflowCacheConfig"):
                workflow_cache_config = WorkflowCacheConfig(
                    _type=details.get("workflowCacheConfig", {}).get("type", ""),
                    value=details.get("workflowCacheConfig", {}).get("value", False),
                    global_value=details.get("workflowCacheConfig", {}).get("global_value", False)
                )
            else:
                workflow_cache_config = None

            ci_pipeline = CiPipeline(
                is_manual=details.get("isManual", False),
                app_id=details.get("appId", 0),
                pipeline_type=details.get("pipelineType", ""),
                name=details.get("name", ""),
                workflow_cache_config=workflow_cache_config,
                external_ci_config=ExternalCiConfig(),
                ci_material=CiPipelineHandlers.get_ci_material(details.get("ciMaterial", [])),
                _id=details.get("id", 0),
                active=details.get("active", False),
                linked_count=details.get("linkedCount", 0),
                scan_enabled=details.get("scanEnabled", False),
                app_workflow_id=details.get("appWorkflowId", 0),
                pre_build_stage=CiPipelineHandlers.get_pre_post_build_config(details.get("preBuildStage", {})),
                post_build_stage=CiPipelineHandlers.get_pre_post_build_config(details.get("postBuildStage", {})),
                is_docker_config_overridden=details.get("isDockerConfigOverridden", False),
                last_triggered_env_id=details.get("lastTriggeredEnvId", 0),
                default_tag=[],
                enable_custom_tag=False,
                docker_args=DockerArgs(),
                custom_tag=CustomTag()
            )
            return {"success": True, "ci_pipeline": ci_pipeline}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def update_current_ci_pipeline(base_url: str, headers: dict, current_ci_pipeline: CiPipeline, ci_config: dict, plugin_metadata: dict, applied_plugin_metadata: list, applied_post_plugin_metadata: list = None):

        try:
            if applied_post_plugin_metadata is None:
                applied_post_plugin_metadata = []
            
            if current_ci_pipeline.pipeline_type == "LINKED":
                return {
                    "success": True,
                    "message": "Linked CI pipeline cannot be updated"
                }
            current_ci_pipeline.is_manual       = ci_config.get("is_manual", current_ci_pipeline.is_manual)
            current_ci_pipeline.pipeline_type   = ci_config.get("type", current_ci_pipeline.pipeline_type)
            current_ci_pipeline.ci_material     = CiPipelineHandlers.update_ci_material(current_ci_pipeline.ci_material, ci_config.get("branches", []))
            current_ci_pipeline.pre_build_stage = CiPipelineHandlers.update_pre_post_build_config(current_ci_pipeline.pre_build_stage, ci_config.get("pre_build_configs", {}).get("tasks", []), plugin_metadata, step_type="PRE_CI", applied_plugin_metadata=applied_plugin_metadata)
            current_ci_pipeline.post_build_stage = CiPipelineHandlers.update_pre_post_build_config(current_ci_pipeline.post_build_stage, ci_config.get("post_build_configs", {}).get("tasks", []), plugin_metadata, step_type="POST_CI", applied_plugin_metadata=applied_post_plugin_metadata)

            patch_result = CiPipelineHandlers.patch_ci_pipeline(base_url, headers, current_ci_pipeline)
            if patch_result["success"]:

                return {"success": True, "message": "CI Pipeline has been updated successfully"}

            return {"success": False, "message": "Failed to update CI Pipeline"}

        except Exception as e:
            print("update_current_ci_pipeline", f"Exception occurred: {str(e)}")
            return {"success": False, "message": str(e)}


    @staticmethod
    def patch_ci_pipeline(base_url, headers, ci: CiPipeline):

        import requests

        payload = {
            "appId": ci.app_id,
            "appWorkflowId": ci.app_workflow_id,
            "action": 1,
            "ciPipeline": {
                "isManual": ci.is_manual,
                "workflowCacheConfig": ci.workflow_cache_config.to_dict(),
                "dockerArgs": ci.docker_args.to_dict(),
                "isExternal": ci.is_external,
                "parentCiPipeline": ci.parent_ci_pipeline,
                "parentAppId": ci.parent_app_id,
                "appId": ci.app_id,
                "externalCiConfig": {
                    "id": 0,
                    "webhookUrl": "",
                    "payload": "",
                    "accessKey": "",
                    "payloadOption": None,
                    "schema": None,
                    "responses": None,
                    "projectId": 0,
                    "projectName": "",
                    "environmentId": "",
                    "environmentName": "",
                    "environmentIdentifier": "",
                    "appId": 0,
                    "appName": "",
                    "role": ""
                },
                "ciMaterial": [material.to_dict() for material in ci.ci_material],
                "name": ci.name,
                "id": ci._id,
                "active": True,
                "linkedCount": ci.linked_count,
                "scanEnabled": ci.scan_enabled,
                "pipelineType": ci.pipeline_type,
                "preBuildStage": ci.pre_build_stage.to_dict(),
                "postBuildStage": ci.post_build_stage.to_dict() if ci.post_build_stage else {},
                "appWorkflowId": ci.app_workflow_id,
                "isDockerConfigOverridden": False,
                "dockerConfigOverride": ci.docker_config_override,
                "lastTriggeredEnvId": 0,
                "defaultTag": ci.default_tag,
                "enableCustomTag": ci.enable_custom_tag,
                "customTag": ci.custom_tag.to_dict(),
            }
        }

        response = requests.post(f"{base_url}/orchestrator/app/ci-pipeline/patch", headers=headers, json=payload)

        if response.status_code != 200:

            return {'success': False, 'error': f"Failed to patch CI pipeline: {response.text}"}
        return {
            "success": True,
            "message": "The Pipeline has been updated"
        }


    @staticmethod
    def get_pre_post_build_plugin_ids(ci_pipeline: CiPipeline) -> list:
        plugin_ids = []
        if ci_pipeline.pre_build_stage:
            for step in ci_pipeline.pre_build_stage.steps:
                # Only collect plugin IDs for REF_PLUGIN steps, skip INLINE/custom steps
                if step.step_type == "REF_PLUGIN" and step.plugin_ref_step_detail:
                    plugin_ids.append(step.plugin_ref_step_detail.plugin_id)

        return plugin_ids