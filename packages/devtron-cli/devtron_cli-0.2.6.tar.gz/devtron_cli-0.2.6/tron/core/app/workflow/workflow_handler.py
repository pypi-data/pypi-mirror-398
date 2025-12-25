import json
import os

import requests
import copy

import yaml

from tron.core.app import BuildConfig
from tron.core.app.env_override_configurations.overrideDeploymentTemplate import EnvOverrideHandler
from tron.core.app.workflow.ci_pipeline.ci_pipeline_handler import CiPipelineHandlers
from tron.core.app.workflow.cd_pipeline.cd_pipeline_handler import CdPipelineHandlers
from tron.utils import DevtronUtils

from jsonmerge import merge


class Workflow:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.DevtronUtils = DevtronUtils(self.base_url, self.headers)
        self.build_config = BuildConfig(self.base_url, self.headers)

    def create_ci_pipeline(self, app_id: int, branches: list, is_manual: bool, pipeline_name: str, build_type: str, pre_build_configs: dict, post_build_configs: dict = None, source_app: str = None, source_pipeline: str = None) -> dict:
        if not app_id or not pipeline_name:
            raise ValueError("app_id and pipeline_name are required parameters.")
        
        # For LINKED builds, branches are not required as they come from source pipeline
        if build_type != "LINKED" and (not branches or not branches):
            raise ValueError("branches are required for non-LINKED build types.")
        
        # Default post_build_configs to empty dict if not provided
        if post_build_configs is None:
            post_build_configs = {}

        api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/ci-pipeline/patch"
        
        # For non-LINKED builds, get git material from current app
        ci_material = []
        if build_type != "LINKED":
            app_details = self.DevtronUtils.get_application_details(app_id)
            if not app_details or "data" not in app_details or "material" not in app_details["data"]:
                raise RuntimeError(f"Failed to fetch git material for app_id {app_id}. Response: {app_details}")
            
            git_material = app_details["data"]["material"]
            ci_material = self.build_ci_material(git_material, branches)
            
            if not ci_material:
                raise RuntimeError("No CI material found. Check your branches and git material configuration.")

        payload = self.build_ci_payload(app_id, ci_material, is_manual, pipeline_name, build_type, pre_build_configs, post_build_configs, source_app, source_pipeline)

        try:
            print(f"Sending request to create CI pipeline '{pipeline_name}' for app ID {app_id}...")
            response = requests.post(api_url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            response_data = response.json()
            print("Successfully created CI pipeline.")
            
            return response_data
        except requests.exceptions.RequestException as err:
            print(f"Request error: {err}")
            raise

    def get_env_id(self, environment_name):
        try:
            print(f"Getting environment ID for: {environment_name}")
            response = requests.get(f'{self.base_url}/orchestrator/env/autocomplete', headers=self.headers)
            if response.status_code == 200:
                environments = response.json().get('result', [])
                for e in environments:
                    if e.get("environment_name") == environment_name:
                        return {
                            'success': True,
                            'environment_id': e.get("id"),
                            'namespace': e.get("namespace")
                        }
                return {'success': False, 'error': f'Environment "{environment_name}" not found'}
            return {'success': False, 'error': f'API request failed: {response.status_code} {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_deployment_strategies(self, app_id: int) -> dict:
        """
        Fetch deployment strategies for an application from the Devtron API.
        
        Args:
            app_id (int): The ID of the application
            
        Returns:
            dict: Result containing the strategies or error message
        """
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/cd-pipeline/strategies/{app_id}"
            response = requests.get(api_url, headers=self.headers)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'strategies': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch deployment strategies: {response.status_code} {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred while fetching deployment strategies: {str(e)}'
            }

    def create_cd_pipeline(self, app_id: int, workflow_id: int, ci_pipeline_id: int, environment_id: int, namespace: str, pipeline_name: str, pre_deploy: dict, post_deploy: dict, deployment_strategies: list = None, deployment_type: str = "helm", is_manual: bool = True, placement: str = "parallel", depends_on: str = None, parent_pipeline_type: str = None, parent_pipeline_id: int = None, run_pre_in_env: bool = False, run_post_in_env: bool = False) -> dict:
        api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/cd-pipeline"
        payload = self.build_cd_pipeline_payload(app_id, workflow_id, ci_pipeline_id, environment_id, namespace, pipeline_name, pre_deploy, post_deploy, deployment_strategies, deployment_type, is_manual, placement, depends_on, parent_pipeline_type, parent_pipeline_id, run_pre_in_env, run_post_in_env)
        
        try:
            response = requests.post(api_url, headers=self.headers, data=json.dumps(payload))
            response.raise_for_status()
            response_data = response.json()
            
            return response_data
        except requests.exceptions.RequestException as err:
            raise err
    
    def create_cd_pipelines_with_dependencies(self, app_id: int, workflow_id: int, ci_pipeline_id: int, cd_pipelines: list) -> dict:
        """
        Create CD pipelines in the correct order based on their dependencies.
        
        Args:
            app_id (int): Application ID
            workflow_id (int): Workflow ID
            ci_pipeline_id (int): CI Pipeline ID
            cd_pipelines (list): List of CD pipeline configurations
            
        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            get_current_cd_pipelines = DevtronUtils.get_cd_pipelines(self.base_url, self.headers, app_id)
            if not get_current_cd_pipelines["success"]:
                return {
                    "success": False,
                    "error": "Failed to get current CD pipelines"
                }
            current_cd_pipelines = get_current_cd_pipelines.get("cd_pipelines", [])
            # Create CD pipelines in the order they were defined
            created_pipelines = {}  #{"environment_name": "pipeline_id"}
            for cd in current_cd_pipelines:
                if cd.get("ciPipelineId") == ci_pipeline_id:
                    created_pipelines[cd.get("environmentName")] = cd.get("id")

            # Build dependency graph and validate dependencies
            dependency_graph = {}
            cd_pipeline_configs = {}
            
            # First pass: Parse all CD pipeline configurations
            for i, c in enumerate(cd_pipelines):
                environment_name = c.get("environment_name")
                pipeline_name = c.get("name", f"cd-pipeline-{i}")
                if not environment_name:
                    return {
                        'success': False,
                        'error': f'CD pipeline at index {i} is missing environment_name'
                    }
                
                # Store configuration using unique key (pipeline name + index to ensure uniqueness)
                # This prevents pipelines with same environment_name from overwriting each other
                unique_key = f"{pipeline_name}_{i}"
                cd_pipeline_configs[unique_key] = c
                depends_on = c.get("depends_on")
                
                # Build dependency graph
                if depends_on:
                    if depends_on not in dependency_graph:
                        dependency_graph[depends_on] = []
                    dependency_graph[depends_on].append(environment_name)
                else:
                    if environment_name not in dependency_graph:
                        dependency_graph[environment_name] = []
            
            # Validate that all dependencies exist in the same workflow
            for c in cd_pipelines:
                depends_on = c.get("depends_on")
                environment_name = c.get("environment_name")
                if depends_on:
                    # Check if any pipeline config has the dependency environment
                    dependency_exists_currently = any(
                        cd.get("environmentName") == depends_on
                        for cd in current_cd_pipelines
                    )
                    dependency_exists = any(
                        config.get("environment_name") == depends_on 
                        for config in cd_pipeline_configs.values()
                    )
                    if not (dependency_exists or dependency_exists_currently):
                        print(f'CD pipeline for environment "{environment_name}" depends on environment "{depends_on}" which is not defined in the same workflow')
                        return {
                            'success': False,
                            'error': f'CD pipeline for environment "{environment_name}" depends on environment "{depends_on}" which is not defined in the same workflow'
                        }
            
            # Topological sort to determine creation order
            creation_order = self._topological_sort(dependency_graph)
            if not creation_order:
                return {
                    'success': False,
                    'error': 'Circular dependency detected in CD pipeline configurations'
                }
            

            
            for unique_key, c in cd_pipeline_configs.items():
                environment_name = c.get("environment_name")
                pipeline_name = c.get("name", f"cd-pipeline-{environment_name}")
                
                print(f"Creating CD pipeline '{pipeline_name}' for environment '{environment_name}'...")
                
                # Get environment details
                env_result = self.get_env_id(environment_name)
                if not env_result['success']:
                    error_msg = f"Failed to create CD pipeline '{pipeline_name}': Could not find environment '{environment_name}' in Devtron. Please ensure the environment exists before creating pipelines. Error: {env_result['error']}"
                    print(f"ERROR: {error_msg}")
                    return {
                        'success': False,
                        'error': error_msg
                    }
                
                environment_id = env_result.get("environment_id", None)
                namespace = env_result.get("namespace", None)
                print(f"Getting environment ID for {environment_name}: {environment_id}")
                
                # Get deployment strategies from CD pipeline configuration
                deployment_strategies = c.get("deployment_strategies", None)
                deployment_type = c.get("deployment_type", "helm")
                is_manual = c.get("is_manual", True)
                placement = c.get("placement", "parallel")
                depends_on = c.get("depends_on", None)
                
                # Prepare pre and post deploy configurations
                pre_deploy = {}
                post_deploy = {}
                pre_deploy_config = c.get("pre_cd_configs", {})
                post_deploy_config = c.get("post_cd_configs", {})
                
                # Handle pre deploy configuration
                if pre_deploy_config:
                    if isinstance(pre_deploy_config, dict) and "tasks" in pre_deploy_config:
                        # New structure with tasks
                        tasks = pre_deploy_config.get("tasks", [])
                        pre_deploy_is_manual = pre_deploy_config.get("is_manual", is_manual)
                        print(f"  Processing {len(tasks)} pre-deploy tasks for pipeline '{pipeline_name}'...")
                        pre_deploy_result = self.create_pre_build_payload(tasks, pre_deploy_is_manual)
                        if not pre_deploy_result.get("success", True):
                            error_msg = f"Failed to create pre-deploy configuration for CD pipeline '{pipeline_name}' in environment '{environment_name}': {pre_deploy_result.get('error', 'Unknown error')}"
                            print(f"ERROR: {error_msg}")
                            return {
                                'success': False,
                                'error': error_msg
                            }
                        pre_deploy = pre_deploy_result
                        print(f"  Successfully configured {len(tasks)} pre-deploy tasks for pipeline '{pipeline_name}'")
                
                # Handle post deploy configuration
                if post_deploy_config:
                    if isinstance(post_deploy_config, dict) and "tasks" in post_deploy_config:
                        # New structure with tasks
                        tasks = post_deploy_config.get("tasks", [])
                        post_deploy_is_manual = post_deploy_config.get("is_manual", is_manual)
                        print(f"  Processing {len(tasks)} post-deploy tasks for pipeline '{pipeline_name}'...")
                        post_deploy_result = self.create_pre_build_payload(tasks, post_deploy_is_manual)
                        if not post_deploy_result.get("success", True):
                            error_msg = f"Failed to create post-deploy configuration for CD pipeline '{pipeline_name}' in environment '{environment_name}': {post_deploy_result.get('error', 'Unknown error')}"
                            print(f"ERROR: {error_msg}")
                            return {
                                'success': False,
                                'error': error_msg
                            }
                        post_deploy = post_deploy_result
                        print(f"  Successfully configured {len(tasks)} post-deploy tasks for pipeline '{pipeline_name}'")
                
                # If this pipeline depends on another, get the parent pipeline ID
                parent_pipeline_id = ci_pipeline_id
                parent_pipeline_type = "CI_PIPELINE"
                if depends_on:
                    if depends_on in created_pipelines:
                        parent_pipeline_id = created_pipelines[depends_on]
                        parent_pipeline_type = "CD_PIPELINE"
                    else:
                        # This shouldn't happen with proper topological sort, but just in case
                        return {
                            'success': False,
                            'error': f'Parent pipeline for environment "{depends_on}" not found during creation of "{environment_name}"'
                        }
                
                # Determine whether to run pre/post deploy tasks in the application env
                # Only supported for pre_cd_configs and post_cd_configs. Default to False.
                run_pre_in_env = bool(pre_deploy_config.get('run_in_app_env', False))
                run_post_in_env = bool(post_deploy_config.get('run_in_app_env', False))

                # Create the CD pipeline
                try:
                    creat_pipeline_status = self.create_cd_pipeline(
                        app_id=app_id,
                        workflow_id=workflow_id,
                        ci_pipeline_id=ci_pipeline_id,
                        environment_id=environment_id,
                        namespace=namespace,
                        pipeline_name=c.get("name", f"cd-pipeline-{environment_name}"),
                        pre_deploy=pre_deploy,
                        post_deploy=post_deploy,
                        deployment_strategies=deployment_strategies,
                        deployment_type=deployment_type,
                        is_manual=is_manual,
                        placement=placement,
                        parent_pipeline_type=parent_pipeline_type,
                        parent_pipeline_id=parent_pipeline_id,
                        run_pre_in_env=run_pre_in_env,
                        run_post_in_env=run_post_in_env
                    )
                    
                    # Store the created pipeline ID for dependencies
                    if creat_pipeline_status.get("code") == 200:
                        pipeline_id = creat_pipeline_status.get("result", {}).get("pipelines", [{}])[0].get("id")
                        if pipeline_id:
                            created_pipelines[environment_name] = pipeline_id
                            print(f"Successfully created CD pipeline '{pipeline_name}' (ID: {pipeline_id}) for environment '{environment_name}'")
                            
                            env_configuration = c.get("env_configuration", {})
                            if env_configuration:
                                # If configuration is provided under env_configuration, it should default to override
                                version = env_configuration.get("deployment_template", {}).get("version", "")
                                # If no version is specified, try to get it from base configuration
                                if not version:
                                    # Get the chart ref ID for the app to determine the version
                                    try:
                                        from tron.core.app.base_configurations.baseDeploymentTemplate import DeploymentTemplateHandler
                                        dt_handler = DeploymentTemplateHandler(self.base_url, self.headers)
                                        base_chart_ref_id = dt_handler.get_latest_chart_ref_id(app_id)
                                        if base_chart_ref_id:
                                            # Fetch chart details to get version
                                            chart_details = self.DevtronUtils._get_chart_details_from_id(app_id, base_chart_ref_id)
                                            if chart_details:
                                                version = chart_details.get('version', '')
                                    except:
                                        pass # If we can't get the version from base, continue without it

                                patch_override_deployement = self.patch_deployment(environment_name, env_configuration, environment_id, namespace, app_id, version)
                                if not patch_override_deployement.get("success", True):
                                    return {
                                        'success': False,
                                        'error': "The pipeline has been created but could not patch the override deployment template"
                                    }
                                else:
                                    print(f"Successfully patched override deployment template for environment {environment_name}")

                                # For config maps and secrets, also handle the type automatically
                                if env_configuration.get("config_maps", []):
                                    config_maps = env_configuration.get("config_maps", [])
                                    for config_map in config_maps:
                                        # Automatically set config_type to override if not specified
                                        
                                        # Handle data/from_file properly with from_file taking precedence
                                        from_file = config_map.get("from_file", "")
                                        data = config_map.get("data", {})
                                        
                                        # If both from_file and data are specified, from_file takes precedence
                                        if from_file:
                                            if not os.path.isfile(from_file):
                                                return {'success': False, 'error': f"Config map file not found: {from_file}"}
                                            with open(from_file, 'r') as f:
                                                file_data = yaml.safe_load(f)
                                                if file_data:  # Only update if file contains data
                                                    config_map["data"] = file_data
                                        elif not data and any(key in config_map for key in ["type", "external", "mountPath", "subPath", "filePermission", "externalType", "roleARN", "esoSecretData", "esoSubPath"]):
                                            # If no data is specified but other values are provided, fetch from base configuration
                                            # Set to override with strategy replace and values from base configuration
                                            config_map["merge_strategy"] = config_map.get("merge_strategy", "replace")
                                            
                                            # Fetch base configuration for this config map to get its data
                                            try:
                                                from tron.core.app.base_configurations.configMapSecret import DevtronConfigMapSecret
                                                cm_secret_handler = DevtronConfigMapSecret(self.base_url, self.headers)
                                                base_config_details = cm_secret_handler.get_config_map_details(app_id, config_map.get("name"))
                                                if base_config_details.get("success"):
                                                    base_data = base_config_details.get("config_map", {}).get("data", {})
                                                    config_map["data"] = base_data
                                                else:
                                                    # If we can't fetch base data, initialize with empty data
                                                    config_map["data"] = {}
                                            except Exception as e:
                                                # If there's an error fetching base config, initialize with empty data
                                                config_map["data"] = {}
                                        
                                        # Check if the config map exists at the base level
                                        try:
                                            from tron.core.app.base_configurations.configMapSecret import DevtronConfigMapSecret
                                            cm_secret_handler = DevtronConfigMapSecret(self.base_url, self.headers)
                                            base_config_details = cm_secret_handler.get_config_map_details(app_id, config_map.get("name"))
                                            if not base_config_details.get("success"):
                                                # If it doesn't exist at base, it's environment-level only
                                                if "merge_strategy" in config_map:
                                                    del config_map["merge_strategy"]
                                        except Exception:
                                            # If there's an error checking, assume it doesn't exist at base
                                            if "merge_strategy" in config_map:
                                                del config_map["merge_strategy"]
                                        
                                        patch_override_config = EnvOverrideHandler.patch_cm_cs(self.base_url, self.headers, app_id, environment_id, "cm", config_map)
                                        if not patch_override_config.get("success", True):
                                            return {
                                                'success': False,
                                                'error': "The pipeline has been created but could not patch the override config map"
                                            }
                                        else:
                                            print(f"Successfully patched override config map for environment {environment_name}")
                                if env_configuration.get("secrets", []):
                                    secrets = env_configuration.get("secrets", [])
                                    for secret in secrets:
                                        # Automatically set config_type to override if not specified
                                        # Handle data/from_file properly with from_file taking precedence
                                        from_file = secret.get("from_file", "")
                                        data = secret.get("data", {})
                                        
                                        # If both from_file and data are specified, from_file takes precedence
                                        if from_file:
                                            if not os.path.isfile(from_file):
                                                return {'success': False, 'error': f"Secret file not found: {from_file}"}
                                            with open(from_file, 'r') as f:
                                                file_data = yaml.safe_load(f)
                                                if file_data: # Only update if file contains data
                                                    secret["data"] = file_data
                                        elif not data and any(key in secret for key in ["type", "external", "mountPath", "subPath", "filePermission", "externalType", "roleARN", "esoSecretData", "esoSubPath"]):
                                            # If no data is specified but other values are provided, fetch from base configuration
                                            # Set to override with strategy replace and values from base configuration
                                            secret["merge_strategy"] = secret.get("merge_strategy", "replace")
                                            
                                            # Fetch base configuration for this secret to get its data
                                            try:
                                                from tron.core.app.base_configurations.configMapSecret import DevtronConfigMapSecret
                                                cm_secret_handler = DevtronConfigMapSecret(self.base_url, self.headers)
                                                base_secret_details = cm_secret_handler.get_secret_details(app_id, secret.get("name"))
                                                if base_secret_details.get("success"):
                                                    base_data = base_secret_details.get("secret", {}).get("data", {})
                                                    secret["data"] = base_data
                                                else:
                                                    # If we can't fetch base data, initialize with empty data
                                                    secret["data"] = {}
                                            except Exception as e:
                                                # If there's an error fetching base config, initialize with empty data
                                                secret["data"] = {}
                                        
                                        # Check if the secret exists at the base level
                                        try:
                                            from tron.core.app.base_configurations.configMapSecret import DevtronConfigMapSecret
                                            cm_secret_handler = DevtronConfigMapSecret(self.base_url, self.headers)
                                            base_secret_details = cm_secret_handler.get_secret_details(app_id, secret.get("name"))
                                            if not base_secret_details.get("success"):
                                                # If it doesn't exist at base, it's environment-level only
                                                if "merge_strategy" in secret:
                                                    del secret["merge_strategy"]
                                        except Exception:
                                            # If there's an error checking, assume it doesn't exist at base
                                            if "merge_strategy" in secret:
                                                del secret["merge_strategy"]
                                        
                                        # Use the same approach for secrets as configmaps - patch them directly
                                        # The API should handle secrets that don't exist in base configuration the same way
                                        patch_override_secret = EnvOverrideHandler.patch_cm_cs(self.base_url, self.headers, app_id, environment_id, "cs", secret)
                                        if not patch_override_secret.get("success", True):
                                            return {
                                                'success': False,
                                                'error': "The pipeline has been created but could not patch the override secret"
                                            }
                                        else:
                                            print(f"Successfully patched override secret for environment {environment_name}")

                        else:
                            return {
                                'success': False,
                                'error': f'Failed to get pipeline ID for environment {environment_name}'
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'Failed to create CD pipeline for environment {environment_name}: {creat_pipeline_status.get("error", "Unknown error")}'
                        }
                        
                except ValueError as e:
                    return {
                        'success': False,
                        'error': f'Failed to create CD pipeline for environment {environment_name}: {str(e)}'
                    }
            
            return {
                'success': True,
                'message': f'Successfully created {len(cd_pipelines)} CD pipelines in dependency order'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred while creating CD pipelines with dependencies: {str(e)}'
            }
    
    def _topological_sort(self, dependency_graph: dict) -> list:
        """
        Perform topological sort on the dependency graph to determine creation order.
        
        Args:
            dependency_graph (dict): Graph representing dependencies between environments
            
        Returns:
            list: Sorted list of environment names in creation order, or empty list if circular dependency
        """
        # Kahn's algorithm for topological sorting
        in_degree = {node: 0 for node in dependency_graph}
        
        # Calculate in-degrees
        for node in dependency_graph:
            for dependent in dependency_graph[node]:
                in_degree[dependent] = in_degree.get(dependent, 0) + 1
        
        # Find all nodes with no incoming edges
        queue = [node for node in in_degree if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Decrease in-degree for all dependents
            for dependent in dependency_graph.get(node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Check for circular dependencies
        if len(result) != len(in_degree):
            return []  # Circular dependency detected
        
        return result


    def get_plugins_details_id(self, appId: int, pluginIds: list) -> dict:
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/plugin/global/list/detail/v2"
            payload = {
                "appId": appId,
                "parentPluginIds": [],
                "pluginIds": pluginIds
            }
            response = requests.post(api_url, headers=self.headers, json=payload)
            data = response.json()
            status_code = data.get("code", 0)
            if status_code == 200:
                plugin_search_result = data.get("result", {})
                if plugin_search_result:
                    plugin_list = plugin_search_result.get("parentPlugins", [])
                    for plugin in plugin_list:
                        plugin_versions = plugin.get('pluginVersions',{}).get('detailedPluginVersionData',[])
                        for version in plugin_versions:
                            if version.get("id") in pluginIds:
                                return version
            return {}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    @staticmethod
    def build_ci_material(git_material: list, branches: list) -> list:
        return [
            {
                "gitMaterialId": git_material[i].get("id"),
                "id": 0,
                "source": {
                    "type": branches[i].get("type"),
                    "value": branches[i].get("branch"),
                    "regex": branches[i].get("regex")
                }
            }
            for i in range(len(branches))
        ]

    def build_ci_payload(self, app_id: int, ci_material: list, is_manual: bool, pipeline_name: str, build_type: str, pre_build_configs: dict, post_build_configs: dict = None, source_app: str = None, source_pipeline: str = None) -> dict:
        """
        Build CI pipeline payload with support for LINKED build type.
        
        Args:
            app_id (int): The ID of the application
            ci_material (list): CI material configuration
            is_manual (bool): Whether the pipeline is manual
            pipeline_name (str): Name of the pipeline
            build_type (str): Type of build (LINKED, etc.)
            pre_build_configs (dict): Pre-build configurations
            post_build_configs (dict): Post-build configurations
            source_app (str): Source application name for LINKED builds
            source_pipeline (str): Source pipeline name for LINKED builds
            
        Returns:
            dict: CI pipeline payload
        """
        # Default post_build_configs to empty dict if not provided
        if post_build_configs is None:
            post_build_configs = {}
        
        payload = {
            "appId": app_id,
            "appWorkflowId": 0,
            "action": 0,
            "ciPipeline": {
                "active": True,
                "ciMaterial": ci_material,
                "dockerArgs": {},
                "externalCiConfig": {},
                "id": 0,
                "isExternal": False,
                "isManual": is_manual,
                "name": pipeline_name,
                "linkedCount": 0,
                "scanEnabled": False,
                "pipelineType": build_type,
                "customTag": {"tagPattern": "", "counterX": 0},
                "workflowCacheConfig": {"type": "INHERIT", "value": True, "globalValue": True},
                "preBuildStage": pre_build_configs,
                "postBuildStage": post_build_configs,
                "dockerConfigOverride": {}
            }
        }
        
        # Handle LINKED build type
        if build_type == "LINKED":
            if not source_pipeline:
                raise ValueError("source_pipeline is required for LINKED build type")
            
            # If source_app is not provided, assume the current app is the source
            source_app_id = app_id
            if source_app:
                # Get source app ID if source_app is provided
                source_app_result = self.DevtronUtils.get_application_id_by_name(source_app)
                if not source_app_result['success']:
                    raise ValueError(f"Could not find source application: {source_app_result['error']}")
                source_app_id = source_app_result['app_id']
            
            # Get source CI pipeline ID
            source_pipeline_result = self.DevtronUtils.get_ci_pipeline_id_by_name(source_app_id, source_pipeline)
            if not source_pipeline_result['success']:
                raise ValueError(f"Could not find source CI pipeline: {source_pipeline_result['error']}")
            source_pipeline_id = source_pipeline_result['ci_pipeline_id']
            
            # Get source CI pipeline details
            pipeline_details_result = self.DevtronUtils.get_ci_pipeline_details(source_app_id, source_pipeline_id)
            if not pipeline_details_result['success']:
                raise ValueError(f"Could not fetch source CI pipeline details: {pipeline_details_result['error']}")
            
            pipeline_details = pipeline_details_result['pipeline_details']
            
            # Get CI material from source pipeline
            source_ci_material = pipeline_details.get('ciMaterial', [])
            if not source_ci_material:
                raise ValueError(f"No CI material found in source pipeline {source_pipeline}")
            
            # Get dockerConfigOverride as-is from pipeline_details
            docker_config_override = pipeline_details.get('dockerConfigOverride', {})
            
            # Update payload for LINKED build type
            payload["ciPipeline"]["isExternal"] = True
            payload["ciPipeline"]["ciMaterial"] = source_ci_material
            payload["ciPipeline"]["dockerConfigOverride"] = docker_config_override
            payload["ciPipeline"]["ciPipelineName"] = source_pipeline
            payload["ciPipeline"]["isDockerConfigOverridden"] = True
            payload["ciPipeline"]["lastTriggeredEnvId"] = -1
            payload["ciPipeline"]["linkedCount"] = 0
            payload["ciPipeline"]["parentAppId"] = 0
            payload["ciPipeline"]["parentCiPipeline"] = source_pipeline_id
            payload["ciPipeline"]["enableCustomTag"] = False
            
            # Add externalCiConfig structure
            payload["ciPipeline"]["externalCiConfig"] = {
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
            }
        
        return payload

    def build_cd_pipeline_payload(self, app_id: int, workflow_id: int, ci_pipeline_id: int, environment_id: int, namespace: str, pipeline_name: str, pre_deploy: dict, post_deploy: dict, deployment_strategies: list = None, deployment_type: str = "helm", is_manual: bool = True, placement: str = "parallel", depends_on: str = None, parent_pipeline_type: str = None, parent_pipeline_id: int = None, run_pre_in_env: bool = False, run_post_in_env: bool = False) -> dict:
        # If deployment_strategies is not provided, fetch from API
        if deployment_strategies is None:
            strategies_result = self.get_deployment_strategies(app_id)
            if strategies_result['success']:
                api_strategies = strategies_result['strategies'].get('result', {}).get('pipelineStrategy', [])
                # Find the default strategy
                default_strategy = None
                for strategy in api_strategies:
                    if strategy.get('default', False):
                        default_strategy = strategy
                        break
                
                # If no default strategy found, use the first one
                if default_strategy is None and api_strategies:
                    default_strategy = api_strategies[0]
                # Convert to the format expected by the API
                if default_strategy:
                    strategies = [self._convert_strategy_format(default_strategy, is_default=True)]
                else:
                    # Fallback to hardcoded ROLLING strategy if API doesn't return any strategies
                    strategies = [self._get_default_rolling_strategy()]
            else:
                # Fallback to hardcoded ROLLING strategy if API call fails
                strategies = [self._get_default_rolling_strategy()]
        else:
            # Validate that only one strategy is marked as default
            default_count = sum(1 for strategy in deployment_strategies if strategy.get('default', False))
            if default_count > 1:
                raise ValueError("Only one strategy can be set to default. Please set only one strategy with default: true")
            
            # Use provided deployment_strategies and convert to API format
            strategies = []
            default_found = False
            for i, strategy in enumerate(deployment_strategies):
                is_default = strategy.get('default', False)
                if is_default:
                    default_found = True
                strategies.append(self._convert_user_strategy(strategy, app_id, is_default))
            
            # If no default strategy was specified, make the first one default
            if strategies and not default_found:
                strategies[0]['default'] = True

        # Set triggerType based on is_manual value
        trigger_type = "MANUAL" if is_manual else "AUTOMATIC"
        
        # Set addType based on placement value, convert to uppercase, default to PARALLEL
        add_type = placement.upper() if placement else "PARALLEL"
        if add_type not in ["SEQUENTIAL", "PARALLEL"]:
            add_type = "PARALLEL"
        
        # Set parent pipeline type and ID
        # If parent_pipeline_type and parent_pipeline_id are provided directly, use them
        # Otherwise, use the depends_on parameter for backward compatibility
        if parent_pipeline_type is not None and parent_pipeline_id is not None:
            final_parent_pipeline_type = parent_pipeline_type
            final_parent_pipeline_id = parent_pipeline_id
        else:
            # Set parent pipeline type and ID based on depends_on parameter
            final_parent_pipeline_type = "CI_PIPELINE"
            final_parent_pipeline_id = ci_pipeline_id
            
            # If depends_on is specified, we need to get the CD pipeline ID for that environment
            # This is for backward compatibility when calling create_cd_pipeline directly
            if depends_on:
                # Get the CD pipeline ID for the environment it depends on
                depends_on_result = self.DevtronUtils.get_cd_pipeline_id_by_environment_name(app_id, depends_on)
                if depends_on_result['success']:
                    final_parent_pipeline_type = "CD_PIPELINE"
                    final_parent_pipeline_id = depends_on_result['pipeline_id']
                else:
                    # If we can't find the CD pipeline, fail the creation
                    raise ValueError(f"Could not find CD pipeline for environment '{depends_on}' that this pipeline depends on. Please ensure the dependent pipeline is created first.")
        
        payload = {
            "appId": app_id,
            "pipelines": [
                {
                    "name": pipeline_name,
                    "appWorkflowId": workflow_id,
                    "ciPipelineId": ci_pipeline_id,
                    "environmentId": environment_id,
                    "namespace": namespace,
                    "id": 0,
                    "strategies": strategies,
                    "parentPipelineType": final_parent_pipeline_type,
                    "parentPipelineId": final_parent_pipeline_id,
                    "isClusterCdActive": False,
                    "deploymentAppType": deployment_type,
                    "deploymentAppName": "",
                    "releaseMode": "create",
                    "deploymentAppCreated": False,
                    "triggerType": trigger_type,
                    "environmentName": namespace,
                    "preStageConfigMapSecretNames": {"configMaps": [], "secrets": []},
                    "postStageConfigMapSecretNames": {"configMaps": [], "secrets": []},
                    "containerRegistryName": "",
                    "repoName": "",
                    "manifestStorageType": "helm_repo",
                    "runPreStageInEnv": bool(run_pre_in_env),
                    "runPostStageInEnv": bool(run_post_in_env),
                    "preDeployStage": pre_deploy,
                    "postDeployStage": post_deploy,
                    "customTag": {},
                    "enableCustomTag": False,
                    "isDigestEnforcedForPipeline": True,
                    "isDigestEnforcedForEnv": False,
                    "addType": add_type
                }
            ]
        }
        
        return payload

    @staticmethod
    def _get_default_rolling_strategy() -> dict:
        """Get the default ROLLING strategy as a fallback."""
        config = {
            "deployment": {
                "strategy": {
                    "rolling": {
                        "maxSurge": "25%",
                        "maxUnavailable": 1
                    }
                }
            }
        }
        return {
            "deploymentTemplate": "ROLLING",
            "defaultConfig": config,
            "config": config,
            "isCollapsed": True,
            "default": True,
            "jsonStr": json.dumps(config, indent=4),
            "yamlStr": "deployment:\n  strategy:\n    rolling:\n      maxSurge: 25%\n      maxUnavailable: 1\n"
        }

    def _convert_strategy_format(self, strategy: dict, is_default: bool = False) -> dict:
        """Convert API strategy format to the format expected by the CD pipeline API."""
        deployment_template = strategy.get('deploymentTemplate', 'ROLLING')
        config = strategy.get('config', {})
        
        # Create defaultConfig from the strategy's default configuration
        default_config = config.copy()
        
        # Convert config to JSON string
        json_str = json.dumps(config, indent=4)
        
        # Convert config to YAML string using the Utils function
        yaml_str = DevtronUtils.convert_dict_to_yaml(config)
        
        return {
            "deploymentTemplate": deployment_template,
            "defaultConfig": default_config,
            "config": config,
            "isCollapsed": True,
            "default": is_default,
            "jsonStr": json_str,
            "yamlStr": yaml_str
        }

    def _convert_user_strategy(self, strategy: dict, app_id: int, is_default: bool = False) -> dict:
        """Convert user-provided strategy to the format expected by the CD pipeline API."""
        
        # Strategy name mapping to handle special cases like BLUE-GREEN
        strategy_name_mapping = {
            'BLUE-GREEN': 'blueGreen',
            'CANARY': 'canary',
            'RECREATE': 'recreate',
            'ROLLING': 'rolling'
        }
        
        # Get strategies from API to get default configurations
        strategies_result = self.get_deployment_strategies(app_id)
        api_strategies = []
        if strategies_result['success']:
            api_strategies = strategies_result['strategies'].get('result', {}).get('pipelineStrategy', [])
        
        name = strategy.get('name', 'ROLLING').upper()  # Convert to uppercase as required
        strategy_config = strategy.get('strategy', {})
        
        # Find the matching strategy in API strategies to get default config
        default_config = {}
        for api_strategy in api_strategies:
            if api_strategy.get('deploymentTemplate', '').upper() == name:
                default_config = api_strategy.get('config', {})
                break
        
        # If no matching API strategy found, we can't proceed
        if not default_config:
            raise ValueError(f"Could not find default configuration for strategy {name} from API")
        
        # Create config by starting with the default config and updating it with user's strategy config
        config = copy.deepcopy(default_config)
        
        # Get the correct strategy key name (camelCase)
        strategy_key = strategy_name_mapping.get(name, name.lower())
        
        # Update the config with user's strategy configuration
        # The user's strategy config should be merged into deployment.strategy.{strategy_name}
        if 'deployment' in config and 'strategy' in config['deployment']:
            if strategy_key in config['deployment']['strategy']:
                # Update the specific strategy configuration with user's values
                for key, value in strategy_config.items():
                    config['deployment']['strategy'][strategy_key][key] = value
            # If the strategy name is not found, we'll use the default config as is
        
        # Convert config to JSON string
        json_str = json.dumps(config, indent=4)
        
        # Convert config to YAML string using the Utils function
        yaml_str = DevtronUtils.convert_dict_to_yaml(config)
        
        result = {
            "deploymentTemplate": name,
            "defaultConfig": default_config,
            "config": config,
            "isCollapsed": False,
            "default": is_default,
            "jsonStr": json_str,
            "yamlStr": yaml_str
        }
        return result

    @staticmethod
    def _merge_user_config_with_default(default_config: dict, user_config: dict, strategy_name: str) -> dict:
        """Merge user configuration with default configuration properly."""
        # Strategy name mapping to handle special cases like BLUE-GREEN
        strategy_name_mapping = {
            'BLUE-GREEN': 'blueGreen',
            'CANARY': 'canary',
            'RECREATE': 'recreate',
            'ROLLING': 'rolling'
        }
        
        merged = copy.deepcopy(default_config)
        
        # For deployment strategies, we need to merge the strategy-specific configuration
        # into the deployment.strategy section
        if strategy_name and user_config:
            # Navigate to the deployment.strategy section
            if 'deployment' in merged and 'strategy' in merged['deployment']:
                strategy_section = merged['deployment']['strategy']
                # Get the correct strategy key name (camelCase)
                strategy_key = strategy_name_mapping.get(strategy_name.upper(), strategy_name.lower())
                # Merge the user config into the specific strategy section
                if strategy_key in strategy_section:
                    strategy_section[strategy_key].update(user_config)
        
        return merged

    @staticmethod
    def build_pre_build_payload(task_name: str, plugin: dict, index: int, plugin_version: int, input_list: dict) -> dict:
        plugin_id = 0
        plugin_versions = plugin.get("pluginVersions", {})
        detailed_plugin_versions = plugin_versions.get("detailedPluginVersionData", []) if plugin_versions else []
        minimal_plugin_versions  = plugin_versions.get("minimalPluginVersionData", []) if plugin_versions else []
        input_variables = []
        for p in minimal_plugin_versions:
            if p.get("pluginVersion", None) == plugin_version:
                plugin_id = p.get("id", 0)
                break
        for p in detailed_plugin_versions:
            if p.get("id", 0) == plugin_id:
                input_variables = p.get("inputVariables", [])
                break
        input_var_data = Workflow.create_input_variable_payload(input_variables, input_list)

        plugin_description = plugin.get("description", "") if plugin else ""

        return {
                    "id": index,
                    "index": index,
                    "name": task_name,
                    "description": plugin_description,
                    "stepType": "REF_PLUGIN",
                    "directoryPath": "",
                    "pluginRefStepDetail": {
                        "id": 0,
                        "pluginId": plugin_id,
                        "conditionDetails": [],
                        "inputVariables": input_var_data,
                        "outputVariables": []
                    }
                }


    def create_pre_build_payload(self, pre_build: list, is_manual: bool = True):

        pre_build_configs = []
        for i in range(len(pre_build)):
            task = pre_build[i]
            task_type = task.get("type", "plugin").lower()
            task_name = task.get("task_name", "")

            if task_type == "custom":
                # Validate custom task
                validation_result = Workflow.validate_custom_task(task, i+1)
                if not validation_result.get("success"):
                    return validation_result
                
                # Build custom step payload
                pre_build_config = Workflow.build_custom_step_payload(task_name, task, i+1)
                pre_build_configs.append(pre_build_config)
            else:
                # Handle plugin type (default)
                plugin_name    = task.get("name", "")
                plugin_version = task.get("version", "")
                input_list     = task.get("input_variables", {})
                
                plugin_req = DevtronUtils.get_plugin_details_by_name(self.base_url, self.headers, plugin_name)
                if not plugin_req.get("success"):
                    return {
                        "success": False,
                        "error": f"Failed to fetch plugin details for {plugin_name}: {plugin_req.get('error', 'Unknown error')}"
                    }
                plugin = plugin_req.get("plugin", {})
                if not plugin:
                    return {
                        "success": False,
                        "error": f"Plugin {plugin_name} not found"
                    }
                pre_build_config = Workflow.build_pre_build_payload(task_name, plugin, i+1, plugin_version, input_list)
                pre_build_configs.append(pre_build_config)
        
        # Set triggerType based on is_manual value
        trigger_type = "MANUAL" if is_manual else "AUTOMATIC"
        
        final_payload = {
            "id": 0,
            "steps": pre_build_configs,
            "triggerType": trigger_type
        }
        
        return final_payload

    @staticmethod
    def create_input_variable_payload(input_variables: list, input_list: dict) -> list:

        input_var_data = []
        if not input_variables:
            return input_var_data

        for _input in input_variables:
            _id = _input.get("id", 0)
            name  = _input.get("name", "")
            value  = input_list.get(name, "")
            description = _input.get("description", "")
            allow_empty_value = _input.get("allowEmptyValue", True)

            i = {
                "allowEmptyValue": allow_empty_value,
                "refVariableName": "",
                "refVariableStage": None,
                "valueConstraint": {
                    "choices": None,
                    "blockCustomValue": False
                },
                "isRuntimeArg": False,
                "defaultValue": "",
                "id": _id,
                "value": value,
                "format": "STRING",
                "name": name,
                "description": description,
                "variableType": "NEW"
            }
            input_var_data.append(i)

        return input_var_data

    @staticmethod
    def create_custom_input_variable_payload(input_variables: list) -> list:
        """
        Create input variable payload for custom/INLINE tasks.
        
        Args:
            input_variables: List of input variable dicts with key, type, value, description
            
        Returns:
            List of formatted input variable dicts
        """
        import random
        input_var_data = []
        if not input_variables:
            return input_var_data

        for var in input_variables:
            key = var.get("key", "")
            var_type = var.get("type", "STRING").upper()
            value = var.get("value", "")
            description = var.get("description", "")
            allow_empty_value = var.get("allow_empty_value", True)

            i = {
                "allowEmptyValue": allow_empty_value,
                "refVariableName": "",
                "refVariableStage": None,
                "valueConstraint": {
                    "choices": None,
                    "blockCustomValue": False
                },
                "isRuntimeArg": False,
                "defaultValue": "",
                "id": random.randint(1000000000000, 9999999999999),
                "value": value,
                "format": var_type,
                "name": key,
                "description": description,
                "variableType": "NEW"
            }
            input_var_data.append(i)

        return input_var_data

    @staticmethod
    def create_custom_output_variable_payload(output_variables: list, existing_vars: dict = None) -> list:
        """
        Create output variable payload for custom/INLINE tasks.
        
        Args:
            output_variables: List of output variable dicts with key, type, description
            existing_vars: Optional dict mapping variable keys to existing IDs
            
        Returns:
            List of formatted output variable dicts
        """
        import random
        output_var_data = []
        if not output_variables:
            return output_var_data
        
        if existing_vars is None:
            existing_vars = {}

        for var in output_variables:
            key = var.get("key", "")
            var_type = var.get("type", "STRING").upper()
            description = var.get("description", "")
            
            # Use existing ID if variable exists, otherwise generate new ID
            var_id = existing_vars.get(key, random.randint(1000000000000, 9999999999999))

            o = {
                "defaultValue": "",
                "id": var_id,
                "value": "",
                "format": var_type,
                "name": key,
                "description": description,
                "variableType": "NEW"
            }
            output_var_data.append(o)

        return output_var_data

    @staticmethod
    def create_condition_details_payload(conditions: list, condition_type: str, existing_conditions: dict = None) -> list:
        """
        Create condition details payload for custom/INLINE tasks.
        
        Args:
            conditions: List of condition dicts with key, operator, value
            condition_type: Either "PASS", "FAIL", or "TRIGGER"
            existing_conditions: Optional dict mapping (condition_type, key) tuples to existing IDs
            
        Returns:
            List of formatted condition dicts
        """
        import random
        condition_data = []
        if not conditions:
            return condition_data
        
        if existing_conditions is None:
            existing_conditions = {}

        for cond in conditions:
            key = cond.get("key", "")
            operator = str(cond.get("operator", "")).strip('"').strip("'")
            value = cond.get("value", "")
            
            # Use existing ID if condition exists, otherwise generate new ID
            cond_id = existing_conditions.get((condition_type, key), random.randint(1000000000000, 9999999999999))

            # Operator should be a plain string
            c = {
                "conditionalValue": value,
                "conditionOnVariable": key,
                "conditionOperator": operator,
                "conditionType": condition_type,
                "id": cond_id
            }
            condition_data.append(c)

        return condition_data

    @staticmethod
    def validate_custom_task(task: dict, index: int) -> dict:
        """
        Validate custom task configuration.
        
        Args:
            task: Task configuration dict
            index: Task index for error messages
            
        Returns:
            Dict with success status and error message if validation fails
        """
        task_name = task.get("task_name", "")
        if not task_name:
            return {
                "success": False,
                "error": f"Task at index {index}: 'task_name' is required for custom type"
            }

        script = task.get("script", "")
        script_type = task.get("script_type", "SHELL" if script else "CONTAINER").upper()
        
        if script_type == "SHELL" and not script:
            return {
                "success": False,
                "error": f"Task '{task_name}' at index {index}: 'script' is required when script_type is SHELL or not specified"
            }

        # Validate that only one of pass_conditions or fail_conditions is specified
        has_pass = task.get("pass_conditions", [])
        has_fail = task.get("fail_conditions", [])
        
        if has_pass and has_fail:
            return {
                "success": False,
                "error": f"Task '{task_name}' at index {index}: Only one of 'pass_conditions' or 'fail_conditions' can be specified, not both"
            }

        # Validate conditions have all required fields
        all_conditions = []
        if has_pass:
            all_conditions.extend([("pass_conditions", c) for c in has_pass])
        if has_fail:
            all_conditions.extend([("fail_conditions", c) for c in has_fail])
        
        for cond_type, cond in all_conditions:
            if not cond.get("key"):
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: '{cond_type}' requires 'key' field"
                }
            if not cond.get("operator"):
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: '{cond_type}' requires 'operator' field"
                }
            if "value" not in cond:
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: '{cond_type}' requires 'value' field"
                }

        # Validate trigger_conditions if present
        trigger_conditions = task.get("trigger_conditions", [])
        for cond in trigger_conditions:
            if not cond.get("key"):
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: 'trigger_conditions' requires 'key' field"
                }
            if not cond.get("operator"):
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: 'trigger_conditions' requires 'operator' field"
                }
            if "value" not in cond:
                return {
                    "success": False,
                    "error": f"Task '{task_name}' at index {index}: 'trigger_conditions' requires 'value' field"
                }

        return {"success": True}

    @staticmethod
    def build_custom_step_payload(task_name: str, task: dict, index: int) -> dict:
        """
        Build payload for custom/INLINE step.
        
        Args:
            task_name: Name of the task
            task: Task configuration dict
            index: Step index
            
        Returns:
            Dict containing the step payload
        """
        description = task.get("description", "")
        script = task.get("script", "")
        container_image = task.get("container_image", "")
        
        # Determine script type - CONTAINER_IMAGE if container_image is specified, otherwise SHELL
        if container_image:
            script_type = "CONTAINER_IMAGE"
        else:
            script_type = task.get("script_type", "SHELL").upper()
        
        # Stringify script
        if script and not isinstance(script, str):
            script = str(script)
        
        # Build input variables
        input_variables = task.get("input_variables", [])
        input_var_data = Workflow.create_custom_input_variable_payload(input_variables)
        
        # Build output variables, conditions - only for non-container tasks
        output_var_data = None
        condition_details = []
        
        if not container_image:
            # Build output variables
            output_variables = task.get("output_variables", [])
            output_var_data = Workflow.create_custom_output_variable_payload(output_variables)
            
            # Build condition details
            # Add trigger conditions as TRIGGER type
            trigger_conditions = task.get("trigger_conditions", [])
            if trigger_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(trigger_conditions, "TRIGGER"))
            
            # Add pass or fail conditions
            pass_conditions = task.get("pass_conditions", [])
            if pass_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(pass_conditions, "PASS"))
            
            fail_conditions = task.get("fail_conditions", [])
            if fail_conditions:
                condition_details.extend(Workflow.create_condition_details_payload(fail_conditions, "FAIL"))
        
        # Build output directory paths (expects array)
        output_directory_paths = task.get("output_directory_paths")
        if output_directory_paths and not isinstance(output_directory_paths, list):
            # If provided but not a list, convert to list
            output_directory_paths = [output_directory_paths]
        
        # Build command args map for container image tasks
        command_args_map = []
        if container_image:
            command = task.get("command", "")
            args = task.get("args", [])
            if command or args:
                command_args_map = [{"command": command, "args": args}]
        else:
            command_args_map = task.get("command_args_map", [{"command": "", "args": []}])
        
        # Build port map for container image tasks
        port_map = []
        if container_image and task.get("ports_mappings"):
            # Parse port mappings like "8080:8090" into {"portOnLocal": 8080, "portOnContainer": 8090}
            for port_mapping in task.get("ports_mappings", []):
                if isinstance(port_mapping, str) and ":" in port_mapping:
                    local_port, container_port = port_mapping.split(":")
                    port_map.append({
                        "portOnLocal": int(local_port.strip()),
                        "portOnContainer": int(container_port.strip())
                    })
                elif isinstance(port_mapping, dict):
                    port_map.append(port_mapping)
        else:
            port_map = task.get("port_map", [])
        
        # Build mount path map for container image tasks
        mount_path_map = []
        if container_image and task.get("directory_mappings"):
            # Parse directory mappings like "/devtroncd:/sourcecode"
            for dir_mapping in task.get("directory_mappings", []):
                if isinstance(dir_mapping, str) and ":" in dir_mapping:
                    host_path, container_path = dir_mapping.split(":")
                    mount_path_map.append({
                        "filePathOnDisk": host_path.strip(),
                        "filePathOnContainer": container_path.strip()
                    })
                elif isinstance(dir_mapping, dict):
                    mount_path_map.append(dir_mapping)
        else:
            mount_path_map = task.get("mount_path_map", [])
        
        # Determine mount options for container tasks
        # mountCodeToContainer: true if script_mount_path_on_container is specified
        # mountDirectoryFromHost: true if directory_mappings is specified
        script_mount_path_on_container = task.get("script_mount_path_on_container") or task.get("mount_code_to_container_path")
        
        if container_image:
            mount_code_to_container = bool(script_mount_path_on_container)
            mount_directory_from_host = bool(mount_path_map)
        else:
            mount_code_to_container = task.get("mount_code_to_container", False)
            mount_directory_from_host = task.get("mount_directory_from_host", False)
        
        # Build inline step detail
        inline_step_detail = {
            "scriptType": script_type,
            "script": script,
            "conditionDetails": condition_details,
            "inputVariables": input_var_data,
            "outputVariables": output_var_data,
            "commandArgsMap": command_args_map,
            "portMap": port_map,
            "mountCodeToContainer": mount_code_to_container,
            "mountDirectoryFromHost": mount_directory_from_host
        }
        
        # Add container-specific fields if container_image is specified
        if container_image:
            inline_step_detail["containerImagePath"] = container_image
            
            # isMountCustomScript: true if script is specified
            inline_step_detail["isMountCustomScript"] = bool(script)
            
            # Add script mount path if script is provided
            if script:
                script_mount_path = task.get("script_mount_path", "/devtroncd/script.sh")
                inline_step_detail["storeScriptAt"] = script_mount_path
                
                # Add mount code to container path if specified
                if script_mount_path_on_container:
                    inline_step_detail["mountCodeToContainerPath"] = script_mount_path_on_container
            
            # Add mount path map if directory_mappings specified
            if mount_path_map:
                inline_step_detail["mountPathMap"] = mount_path_map
        
        step_payload = {
            "id": index,
            "index": index,
            "name": task_name,
            "description": description,
            "stepType": "INLINE",
            "directoryPath": "",
            "inlineStepDetail": inline_step_detail,
            "outputDirectoryPath": output_directory_paths
        }
        
        return step_payload

    def delete_workflow(self, base_url: str, headers: dict, app_id: int, workflow_id: int) -> dict:
        """
        Delete a workflow by ID (only works if workflow is empty).

        Args:
            base_url (str): The base URL of the Devtron instance
            headers (dict): The headers for authentication
            app_id (int): The ID of the application
            workflow_id (int): The ID of the workflow to delete

        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            api_url = f"{base_url.rstrip('/')}/orchestrator/app/app-wf/{app_id}/{workflow_id}"
            print(f"Deleting workflow ID {workflow_id} for app ID {app_id}...")

            response = requests.delete(api_url, headers=headers)

            if response.status_code == 200:
                print(f"Successfully deleted workflow ID {workflow_id}")
                return {
                    'success': True,
                    'message': f'Workflow ID {workflow_id} deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to delete workflow {workflow_id}: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def update_cd_pipeline(self, app_id: int, cd_pipeline_id: int, updated_pipeline_data: dict) -> dict:
        """
        Update a CD pipeline using PATCH endpoint.
        
        Args:
            app_id (int): The ID of the application
            cd_pipeline_id (int): The ID of the CD pipeline to update
            updated_pipeline_data (dict): The updated pipeline data
            
        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/cd-pipeline/patch"
            print(f"Updating CD pipeline ID {cd_pipeline_id} for app ID {app_id}...")

            payload = {
                "action": 2,  # Update action
                "appId": app_id,
                "pipeline": updated_pipeline_data
            }

            response = requests.post(api_url, headers=self.headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'result': result
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to update CD pipeline: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def delete_ci_pipeline(self, base_url: str, headers: dict, app_id: int, app_workflow_id: int, ci_pipeline_id: int,
                           ci_pipeline_name: str) -> dict:
        """
        Delete a CI pipeline using PATCH endpoint.

        Args:
            base_url (str): The base URL of the Devtron instance
            headers (dict): The headers for authentication
            app_id (int): The ID of the application
            app_workflow_id (int): The ID of the workflow
            ci_pipeline_id (int): The ID of the CI pipeline to delete
            ci_pipeline_name (str): The name of the CI pipeline to delete

        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            api_url = f"{base_url.rstrip('/')}/orchestrator/app/ci-pipeline/patch"
            print(f"Deleting CI pipeline ID {ci_pipeline_id} for app ID {app_id}...")

            payload = {
                "action": 2,  # Delete action
                "appId": app_id,
                "appWorkflowId": app_workflow_id,
                "ciPipeline": {
                    "id": ci_pipeline_id,
                    "name": ci_pipeline_name
                }
            }

            response = requests.post(api_url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()
                ci_pipelines = result.get('result', {}).get('ciPipelines', [])
                deleted_pipeline = None
                for pipeline in ci_pipelines:
                    if pipeline.get('id') == ci_pipeline_id and pipeline.get('deleted', False):
                        deleted_pipeline = pipeline
                        break

                if deleted_pipeline:
                    print(f"Successfully deleted CI pipeline ID {ci_pipeline_id}")
                    return {
                        'success': True,
                        'message': f'CI pipeline ID {ci_pipeline_id} deleted successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to confirm deletion of CI pipeline {ci_pipeline_id}'
                    }
            else:
                return {
                    'success': False,
                    'error': f'Failed to delete CI pipeline: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def delete_cd_pipeline(self, base_url: str, headers: dict, app_id: int, cd_pipeline_id: int) -> dict:
        """
        Delete a CD pipeline using PATCH endpoint.

        Args:
            base_url (str): The base URL of the Devtron instance
            headers (dict): The headers for authentication
            app_id (int): The ID of the application
            cd_pipeline_id (int): The ID of the CD pipeline to delete

        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            api_url = f"{base_url.rstrip('/')}/orchestrator/app/cd-pipeline/patch"
            print(f"Deleting CD pipeline ID {cd_pipeline_id} for app ID {app_id}...")

            payload = {
                "action": 1,  # Delete action
                "appId": app_id,
                "pipeline": {
                    "id": cd_pipeline_id
                }
            }

            response = requests.post(api_url, headers=headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()
                pipelines = result.get('result', {}).get('pipelines', [])
                if pipelines and 'deleteResponse' in result.get('result', {}):
                    delete_response = result['result']['deleteResponse']
                    if delete_response.get('deleteInitiated', False):
                        print(f"Successfully deleted CD pipeline ID {cd_pipeline_id}")
                        return {
                            'success': True,
                            'message': f'CD pipeline ID {cd_pipeline_id} deleted successfully'
                        }

                return {
                    'success': False,
                    'error': f'Failed to confirm deletion of CD pipeline {cd_pipeline_id}'
                }
            else:
                try:
                    error_json = response.json()
                    errors = error_json.get('errors', [])
                    user_message = None
                    if errors:
                        # Extract userMessage from the first error
                        user_message = errors[0].get('userMessage') or errors[0].get('internalMessage')
                    
                    if user_message:
                        return {
                            'success': False,
                            'error': f'Failed to delete CD pipeline {cd_pipeline_id}: {user_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Failed to delete CD pipeline: {response.text}'
                        }
                except json.JSONDecodeError:
                    # If response is not valid JSON, return the raw text
                    return {
                        'success': False,
                        'error': f'Failed to delete CD pipeline: {response.text}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }
    def get_base_deployment_template_values(self, app_id: int, environment_id: int, chart_ref_id: int) -> dict:
        """
        Get the base deployment template values using the base configuration handler.
        """
        try:
            from tron.core.app.base_configurations.baseDeploymentTemplate import DeploymentTemplateHandler
            # Create a temporary handler to access the method
            dt_handler = DeploymentTemplateHandler(self.base_url, self.headers)
            result = dt_handler.get_deployment_template_yaml(app_id, chart_ref_id)
            if result['success']:
                # Return the globalConfig.defaultAppOverride values which are the base values
                base_values = result['yaml'].get('globalConfig', {}).get('defaultAppOverride', {})
                return {'success': True, 'values': base_values}
            else:
                return result
        except Exception as e:
            return {'success': False, 'error': str(e)}


    def patch_deployment(self, environment_name, env_configuration: dict, environment_id, namespace, app_id, version: str) -> dict:
        """
        Patch deployment template with new logic based on tasks requirements.
        
        Args:
            environment_name (str): Environment name
            env_configuration (dict): Environment configuration
            environment_id (int): Environment ID
            namespace (str): Namespace
            app_id (int): Application ID
            version (str): Chart version
            
        Returns:
            dict: Result of the operation
        """
        try:
            deployment_template_config = env_configuration.get("deployment_template", {})
            if deployment_template_config.get("chart_type"):
                print(f"Warning: chart_type cannot be specified under env_configuration.deployment_template and will be ignored. Environment-specific configurations automatically inherit the chart type from base configurations.")
            
            # Extract parameters
            app_metrics = deployment_template_config.get("show_application_metrics", False)
            merge_strategy = deployment_template_config.get("merge_strategy", "replace")  # Task 3: Default to replace
            values_patch = deployment_template_config.get("values_patch", {})
            values_path = deployment_template_config.get("values_path", "")
            
            env_override = {}
            if values_path:
                # Task 2: values_path takes precedence
                if not os.path.isfile(values_path):
                    return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                with open(values_path, 'r') as f:
                    env_override = yaml.safe_load(f)
                env_override = self._remove_newlines_from_strings(env_override)
            elif values_patch:
                if merge_strategy == "patch":
                    # Use values_patch as is without merging
                    env_override = values_patch
                elif merge_strategy == "replace":
                    # Merge values_patch with base configuration values for replace strategy
                    current_chart_ref_id = self.get_chart_ref_id_by_environment_id(app_id, environment_id)
                    if current_chart_ref_id == -1:
                        return {'success': False, 'error': f"Failed to fetch chart ref ID for environment ID {environment_id}"}
                    
                    # Get base configuration values
                    base_config_result = self.get_base_deployment_template_values(app_id, environment_id, current_chart_ref_id)
                    if not base_config_result['success']:
                        return {'success': False, 'error': f"Failed to fetch base deployment template values: {base_config_result['error']}"}
                    
                    base_values = base_config_result.get('values', {})
                    # Merge values_patch with base values using jsonmerge
                    env_override = merge(base_values, values_patch)
            else:
                # If no values are specified under deployment template but other values exist, use base configuration values
                merge_strategy = "replace" # Default to replace if not provided
                current_chart_ref_id = self.get_chart_ref_id_by_environment_id(app_id, environment_id)
                if current_chart_ref_id == -1:
                    return {'success': False, 'error': f"Failed to fetch chart ref ID for environment ID {environment_id}"}
                
                # Get base configuration values
                base_config_result = self.get_base_deployment_template_values(app_id, environment_id, current_chart_ref_id)
                if not base_config_result['success']:
                    return {'success': False, 'error': f"Failed to fetch base deployment template values: {base_config_result['error']}"}
                
                env_override = base_config_result.get('values', {})
            
            # Get chart ref ID and config ID
            current_chart_ref_id = self.get_chart_ref_id_by_environment_id(app_id, environment_id)
            if current_chart_ref_id == -1:
                return {'success': False, 'error': f"Failed to fetch chart ref ID for environment ID {environment_id}"}
            
            chart_ref_id = self.get_chart_ref_id_by_version(version, current_chart_ref_id, app_id, environment_id)
            config_id = self.get_config_id(app_id, environment_id, chart_ref_id)
            
            # Build and send payload
            payload = self.build_configuration_payload(environment_name, environment_id, chart_ref_id, is_override=True, app_metrics=app_metrics, merge_strategy=merge_strategy, env_override=env_override, namespace=namespace, config_id=config_id)
            
            if config_id:
                api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/env"
                response = requests.put(api_url, headers=self.headers, data=json.dumps(payload))
            else:
                api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/env/{app_id}/{environment_id}"
                response = requests.post(api_url, headers=self.headers, data=json.dumps(payload))

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print(f"Successfully patched deployment template for environment {environment_name}")
                    return {'success': True, 'message': 'Deployment template patched successfully'}
                else:
                    return {'success': False, 'error': f"Failed to patch deployment template: {result.get('error', 'Unknown error')}"}
            else:
                return {'success': False, 'error': f"Failed to patch deployment template: {response.text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}



    def _remove_newlines_from_strings(self, obj):
            if isinstance(obj, dict):
                return {k: self._remove_newlines_from_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._remove_newlines_from_strings(i) for i in obj]
            elif isinstance(obj, str):
                return obj.replace('\n', '')
            else:
                return obj


    def get_chart_ref_id_by_version(self, version, current_chart_ref_id, app_id, environment_id):
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/chartref/autocomplete/{app_id}/{environment_id}"
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    chart_refs = result.get('result', {}).get("chartRefs", [])
                    chart_name = ""
                    for chart in chart_refs:
                        if chart.get("id", "") == current_chart_ref_id:
                            chart_name = chart.get("name", "")
                    for chart in chart_refs:
                        if chart.get("version", "") == version and chart.get("name", "") == chart_name:
                            return chart.get("id", 0)

            return 0
        except Exception as e:
            print(f"Exception occurred while fetching chart versions: {str(e)}")
            return 0


    def get_config_id(self, app_id, environment_id, chart_ref_id):
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/env/{app_id}/{environment_id}/{chart_ref_id}"
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    config_data = result.get('result', {}).get("environmentConfig", {})
                    return config_data.get("id", 0)
            return 0
        except Exception as e:
            print(f"Exception occurred while fetching config ID: {str(e)}")
            return 0

    def get_chart_ref_id_by_environment_id(self, app_id, environment_id):
        try:
            api_url = f"{self.base_url.rstrip('/')}/orchestrator/app/other-env/min?app-id={app_id}"
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    chart_ref_data = result.get('result', [])
                    for data in chart_ref_data:
                        if data.get("environmentId", -1) == environment_id:
                            return data.get("chartRefId", 0)
            return -1
        except Exception as e:
            print(f"Exception occurred while fetching chart ref ID: {str(e)}")
            return -1

    @staticmethod
    def build_configuration_payload(environment_name: str, environment_id: int, chart_ref_id: int, is_override: bool,  app_metrics: bool, merge_strategy: str, env_override: dict, namespace: str, config_id: int, save_eligible_changes:bool = True, status: int = 1) -> dict:
        if config_id != 0:
            return {
                "environmentId": environment_id,
                "chartRefId": chart_ref_id,
                "IsOverride": is_override,
                "isAppMetricsEnabled": app_metrics,
                "saveEligibleChanges": save_eligible_changes,
                "id": config_id,
                "status": status,
                "manualReviewed": True,
                "active": True,
                "namespace": namespace,
                "mergeStrategy": merge_strategy,
                "envOverrideValues": env_override,
                "isExpressEdit": False,
                "resourceName": f"{environment_name}-DeploymentTemplateOverride"
            }
        else:
            return {
                "environmentId": environment_id,
                "chartRefId": chart_ref_id,
                "IsOverride": is_override,
                "isAppMetricsEnabled": app_metrics,
                "saveEligibleChanges": save_eligible_changes,
                "mergeStrategy": merge_strategy,
                "envOverrideValues": env_override,
                "isExpressEdit": False,
                "resourceName": f"{environment_name}-DeploymentTemplateOverride"
            }



    def update_workflows(self, config_data, allow_deletion) -> dict:
        try:
            print("CAUTION: If you have used --allow-deletion flag this this might delete the CD Pipelines not present in config file along with it's resources!!")
            app_name = config_data.get("app_name")
            if not app_name:
                return {'success': False, 'error': "Application name not found in config_data."}

            app_id_response = self.DevtronUtils.get_application_id_by_name(app_name)
            app_id = app_id_response.get("app_id", 0)

            if not app_id:
                return {'success': False, 'error': f"Application with name '{app_name}' not found."}

            get_workflows = requests.get(f"{self.base_url}/orchestrator/app/app-wf/{app_id}", headers=self.headers)
            get_ci_pipelines = requests.get(f"{self.base_url}/orchestrator/app/ci-pipeline/{app_id}", headers=self.headers)

            if get_workflows.status_code != 200 or get_ci_pipelines.status_code != 200:
                return {'success': False, 'error': f"Failed to fetch existing workflows: {get_workflows.text}"}

            existing_workflows_data = get_workflows.json().get("result", []).get("workflows", [])
            existing_ci_pipelines_data = get_ci_pipelines.json().get("result", {})

            # Create a mapping from CI pipeline component ID to its name
            existing_ci_id_to_name = {
                ci_pipeline.get("id"): ci_pipeline.get("name")
                for ci_pipeline in existing_ci_pipelines_data.get("ciPipelines", [])
            }
            ci_name_to_id = {name: id for id, name in existing_ci_id_to_name.items()}


            # Create a set of existing CI pipeline names from the `existing_workflows` tree
            existing_ci_pipeline_names = set()
            for workflow in existing_workflows_data:
                ci_pipeline_node = next(
                    (node for node in workflow.get("tree", []) if node.get("type") == "CI_PIPELINE"), None)
                if ci_pipeline_node and ci_pipeline_node.get("componentId") in existing_ci_id_to_name:
                    ci_name = existing_ci_id_to_name[ci_pipeline_node.get("componentId")]
                    existing_ci_pipeline_names.add(ci_name)

            existing_ci_name_to_workflow = {}
            for workflow in existing_workflows_data:
                ci_pipeline_node = next(
                    (node for node in workflow.get("tree", []) if node.get("type") == "CI_PIPELINE"), None)
                if ci_pipeline_node and ci_pipeline_node.get("componentId") in existing_ci_id_to_name:
                    ci_name = existing_ci_id_to_name[ci_pipeline_node.get("componentId")]
                    existing_ci_name_to_workflow[ci_name] = workflow

            config_ci_pipeline_names = {
                wf.get("ci_pipeline", {}).get("name")
                for wf in config_data.get("workflows", [])
            }


            workflows_to_create = [
                ci_name for ci_name in config_ci_pipeline_names
                if ci_name not in existing_ci_pipeline_names
            ]


            workflows_to_update = [
                ci_name for ci_name in config_ci_pipeline_names
                if ci_name in existing_ci_pipeline_names
            ]


            workflows_to_delete = [
                ci_name for ci_name in existing_ci_pipeline_names
                if ci_name not in config_ci_pipeline_names
            ]
            if workflows_to_create:
                for ci in workflows_to_create:
                    for wf in config_data.get("workflows", []):
                        if wf.get("ci_pipeline", {}).get("name") == ci:
                            creation_result = self.create_workflow(wf, app_id)
                            if not creation_result.get("success"):
                                return creation_result
            if workflows_to_update:
                for ci in workflows_to_update:
                    for wf in config_data.get("workflows", []):
                        if wf.get("ci_pipeline", {}).get("name") == ci:
                            ci_pipeline_id = ci_name_to_id.get(wf.get("ci_pipeline", {}).get("name", ""))
                            update_result = self.update_workflow(wf, app_id, ci_pipeline_id, allow_deletion)
                            if not update_result.get("success"):
                                return {
                                    "success": False,
                                    "error": update_result.get("error", update_result.get("message", "Failed to update workflow"))
                                }

            if workflows_to_delete and allow_deletion:
                for ci in workflows_to_delete:
                    data = existing_ci_name_to_workflow.get(ci, {})
                    workflow_id = data.get("id", 0)
                    delete_workflow_result = self.delete_workflow_iteratively(app_id, workflow_id, data)
                    if not delete_workflow_result.get("success"):
                        return delete_workflow_result
            elif workflows_to_delete and not allow_deletion:
                print(f"Workflows to delete (not deleted, --allow-deletion not set): {workflows_to_delete}")

            return {
                'success': True,
                'message': 'Workflows updated successfully.',
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_workflow(self, w, app_id):

        ci_pipeline       = w.get("ci_pipeline", {})

        pre_build         = ci_pipeline.get("pre_build_configs", [])
        post_build        = ci_pipeline.get("post_build_configs", [])
        pipeline_name     = ci_pipeline.get("name", "")
        is_manual         = ci_pipeline.get("is_manual", False)
        build_type        = ci_pipeline.get("type", "")
        source_app        = ci_pipeline.get("source_app")
        source_pipeline   = ci_pipeline.get("source_pipeline")
        pre_build_configs = {}
        post_build_configs = {}
        
        if pre_build and "tasks" in pre_build:
            tasks = pre_build.get("tasks", [])
            pre_build_configs = self.create_pre_build_payload(tasks)
        
        if post_build and "tasks" in post_build:
            tasks = post_build.get("tasks", [])
            post_build_configs = self.create_pre_build_payload(tasks)


        # For LINKED builds, branches are not required
        branch_data = []
        if build_type != "LINKED":
            branch_data = w["ci_pipeline"]["branches"]

        if not pipeline_name:
            return {
                'success': False,
                'error': 'ci_pipeline.name is required in config'
            }

        workflow_creation = self.create_ci_pipeline(
            app_id=app_id,
            pipeline_name=pipeline_name,
            branches=branch_data,
            is_manual=is_manual,
            build_type=build_type,
            pre_build_configs=pre_build_configs,
            post_build_configs=post_build_configs,
            source_app=source_app,
            source_pipeline=source_pipeline
        )

        if workflow_creation["code"] != 200:
            return {
                "success": False,
                "error": f"Application created but failed to create workflow: {workflow_creation['error']}"
            }
        print(f"Workflow '{pipeline_name}' created successfully.")

        cd_pipelines = w.get("cd_pipelines", [])
        if cd_pipelines:
            workflow_id = workflow_creation.get("result", {}).get("appWorkflowId", 0)
            ci_pipelines = workflow_creation.get("result", {}).get("ciPipelines", [])
            ci_pipeline_id = ci_pipelines[0].get("id", 0) if ci_pipelines else 0

            # Handle CD pipeline creation with dependency management
            cd_creation_result = self.create_cd_pipelines_with_dependencies(
                app_id=app_id,
                workflow_id=workflow_id,
                ci_pipeline_id=ci_pipeline_id,
                cd_pipelines=cd_pipelines
            )

            if not cd_creation_result['success']:
                return cd_creation_result
        return {
            'success': True,
            'message': f'Workflow {pipeline_name} created successfully'
        }


    def delete_workflow_iteratively(self, app_id: int, workflow_id: int, data: dict) -> dict:
        get_ci_pipelines = requests.get(f"{self.base_url}/orchestrator/app/ci-pipeline/{app_id}", headers=self.headers)
        get_cd_pipelines = requests.get(f"{self.base_url}/orchestrator/app/cd-pipeline/{app_id}", headers=self.headers)
        if get_ci_pipelines.status_code != 200 or get_cd_pipelines.status_code != 200:
            return {'success': False, 'error': f"Failed to fetch existing pipelines: {get_ci_pipelines.text}, {get_cd_pipelines.text}"}

        ci_pipelines_id = []
        cd_pipelines_id = []
        for node in data.get("tree", []):
            if node.get("type") == "CI_PIPELINE":
                ci_pipelines_id.append(node.get("componentId", 0))
            elif node.get("type") == "CD_PIPELINE":
                cd_pipelines_id.append(node.get("componentId", 0))
        for cd in cd_pipelines_id:
            delete_cd_result = self.delete_cd_pipeline(self.base_url, self.headers, app_id, cd)
            if not delete_cd_result.get("success"):
                return delete_cd_result

        for ci in ci_pipelines_id:
            ci_pipelines = get_ci_pipelines.json().get("result", {}).get("ciPipelines", [])
            for pipeline in ci_pipelines:
                if pipeline.get("id", "") == ci:
                    ci_name = pipeline.get("name", "")
                    break
            delete_ci_result = self.delete_ci_pipeline(self.base_url, self.headers, app_id, workflow_id, ci, ci_name)
            if not delete_ci_result.get("success"):
                return delete_ci_result
        delete_workflow_result = self.delete_workflow(self.base_url, self.headers, app_id, workflow_id)
        if not delete_workflow_result.get("success"):
            return delete_workflow_result

        return {
            "success": True,
            "deleted_children": [],
            "failed_deletion_children": []
        }


    def update_workflow(self, w, app_id, ci_pipeline_id, allow_deletion):
        try:

            ci_config = w.get("ci_pipeline", {})
            plugins = ci_config.get("pre_build_configs", {}).get("tasks", [])
            post_plugins = ci_config.get("post_build_configs", {}).get("tasks", [])
            applied_plugin_metadata = []
            applied_post_plugin_metadata = []
            if plugins:
                for plugin in plugins:
                    # Only process plugin types, skip custom types
                    plugin_type = plugin.get("type", "plugin").lower()
                    if plugin_type == "plugin":
                        plugin_name = plugin.get("name", "")
                        if not plugin_name:
                            continue
                        plugin_details_result = DevtronUtils.get_plugin_details_by_name(self.base_url, self.headers, plugin_name)
                        if not plugin_details_result["success"]:
                            return {
                                "success": False,
                                "error": f"Plugin '{plugin_name}' not found"
                            }
                        applied_plugin_metadata.append(plugin_details_result.get("plugin", ""))
            
            if post_plugins:
                for plugin in post_plugins:
                    # Only process plugin types, skip custom types
                    plugin_type = plugin.get("type", "plugin").lower()
                    if plugin_type == "plugin":
                        plugin_name = plugin.get("name", "")
                        if not plugin_name:
                            continue
                        plugin_details_result = DevtronUtils.get_plugin_details_by_name(self.base_url, self.headers, plugin_name)
                        if not plugin_details_result["success"]:
                            return {
                                "success": False,
                                "error": f"Plugin '{plugin_name}' not found"
                            }
                        applied_post_plugin_metadata.append(plugin_details_result.get("plugin", ""))


            get_ci = CiPipelineHandlers.get_ci_pipeline(self.base_url, self.headers, app_id, ci_pipeline_id)

            if not get_ci["success"]:
                return {
                    "success": False,
                    "error": f"Failed to fetch CI pipeline details: {get_ci['error']}"
                }
            current_ci_pipeline = get_ci.get("ci_pipeline")

            pipeline_plugin_ids = CiPipelineHandlers.get_pre_post_build_plugin_ids(current_ci_pipeline)
            plugin_metadata = {}
            if pipeline_plugin_ids:
                plugin_metadata_response = DevtronUtils.get_plugin_details_by_id(self.base_url, self.headers, pipeline_plugin_ids, app_id)
                if not plugin_metadata_response["success"]:
                    return {
                        "success": False,
                        "error": "Plugin metadata not found"
                    }
                plugin_metadata = plugin_metadata_response.get("plugin_data", {})
            updated_ci_pipeline = CiPipelineHandlers.update_current_ci_pipeline(self.base_url, self.headers, current_ci_pipeline, ci_config, plugin_metadata, applied_plugin_metadata, applied_post_plugin_metadata)
            if not updated_ci_pipeline["success"]:
                print(f"Failed to update CI pipeline")
                return {
                    "success": False,
                    "error": updated_ci_pipeline.get("message", "Failed to update ci pipeline")
                }

            ci_pipeline_id_result = CiPipelineHandlers.get_ci_id_using_name(self.base_url, self.headers, w.get("ci_pipeline", {}).get("name", ""), app_id)
            if not ci_pipeline_id_result["success"]:
                print(f"Failed to get CI pipeline ID")
                return {
                    "success": False,
                    "error": ci_pipeline_id_result.get("error", "Failed to get CI pipeline ID")
                }
            ci_pipeline_id = ci_pipeline_id_result.get("ci_pipeline_id", 0)

            handle_cd_pipeline_result = self.handle_cd_pipelines(self.base_url, self.headers, app_id, w, ci_pipeline_id, allow_deletion)
            if not handle_cd_pipeline_result["success"]:
                print(f"Failed to handle CD pipelines")
                return {
                    "success": False,
                    "error": handle_cd_pipeline_result.get("error", "Failed to handle CD pipelines")
                }

            # Update CD pipelines
            cd_pipelines_config = w.get("cd_pipelines", [])
            if cd_pipelines_config:
                # Get existing CD pipelines for this CI pipeline
                get_cd_pipelines = requests.get(f"{self.base_url}/orchestrator/app/cd-pipeline/{app_id}", headers=self.headers)
                if get_cd_pipelines.status_code == 200:
                    existing_cd_pipelines = get_cd_pipelines.json().get("result", {}).get("pipelines", [])
                    
                    # Create a mapping of environment name to existing CD pipeline
                    existing_cd_by_env = {}
                    for pipeline in existing_cd_pipelines:
                        if pipeline.get("ciPipelineId") == ci_pipeline_id:
                            existing_cd_by_env[pipeline.get("environmentName")] = pipeline
                    
                    # Update each CD pipeline in the config
                    for cd_config in cd_pipelines_config:
                        environment_name = cd_config.get("environment_name")
                        if environment_name in existing_cd_by_env:
                            existing_cd_pipeline = existing_cd_by_env[environment_name]
                            cd_pipeline_id = existing_cd_pipeline.get("id")
                            
                            # Check if deployment strategies need to be updated
                            deployment_strategies_config = cd_config.get("deployment_strategies")
                            # Compare deployment strategies (including case where strategies are removed)
                            existing_strategies = existing_cd_pipeline.get("strategies", [])
                            strategies_differ = self._compare_deployment_strategies(existing_strategies, deployment_strategies_config)
                            
                            if strategies_differ:
                                # Update the CD pipeline with new deployment strategies
                                updated_pipeline_data = existing_cd_pipeline.copy()
                                updated_pipeline_data["strategies"] = self._build_updated_strategies(existing_strategies, deployment_strategies_config, app_id)
                                
                                # Remove fields that shouldn't be sent in the update
                                updated_pipeline_data.pop("deploymentAppDeleteRequest", None)
                                updated_pipeline_data.pop("clusterName", None)
                                updated_pipeline_data.pop("environmentIdentifier", None)
                                updated_pipeline_data.pop("lastDeployedEnvironmentImage", None)
                                updated_pipeline_data.pop("userApprovalConfig", None)
                                updated_pipeline_data.pop("isVirtualEnvironment", None)
                                
                                update_result = self.update_cd_pipeline(app_id, cd_pipeline_id, updated_pipeline_data)
                                if not update_result["success"]:
                                    return {
                                        "success": False,
                                        "error": f"Failed to update CD pipeline for environment {environment_name}: {update_result['error']}"
                                    }
                                print(f"Updated CD pipeline for environment {environment_name}")

            return {
                'success': True,
                'message': "Workflow updated successfully."
            }


        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _compare_deployment_strategies(self, existing_strategies: list, config_strategies: list) -> bool:
        """
        Compare existing deployment strategies with configured strategies to check if they differ.
        
        Args:
            existing_strategies (list): Existing deployment strategies from the CD pipeline
            config_strategies (list): Configured deployment strategies from the YAML
            
        Returns:
            bool: True if strategies differ, False otherwise
        """
        try:
            # Handle case where config_strategies is None (not specified in config)
            # In this case, we should not update the strategies at all
            if config_strategies is None:
                return False
            
            # Handle case where config_strategies is an empty list (explicitly set to empty in config)
            # In this case, we should update to use default strategies
            if not config_strategies:
                # If existing strategies exist but config has none, they differ
                return len(existing_strategies) > 0
            
            # Create a mapping of deployment template to strategy for both existing and config
            existing_strategy_map = {strategy.get("deploymentTemplate"): strategy for strategy in existing_strategies}
            config_strategy_map = {}
            for strategy in config_strategies:
                name = strategy.get("name")
                if name:
                    config_strategy_map[name.upper()] = strategy
            
            # Check if number of strategies differ
            if len(existing_strategy_map) != len(config_strategy_map):
                return True
            
            # Check if any configured strategy differs from existing
            for template_name, config_strategy in config_strategy_map.items():
                if template_name in existing_strategy_map:
                    existing_strategy = existing_strategy_map[template_name]
                    config_strategy_details = config_strategy.get("strategy", {})
                    existing_config = existing_strategy.get("config", {})
                    
                    # Compare the strategy configuration using deepdiff
                    if "deployment" in existing_config and "strategy" in existing_config["deployment"]:
                        existing_strategy_details = existing_config["deployment"]["strategy"]
                        
                        # Handle special cases using the same mapping as in _convert_user_strategy
                        strategy_name_mapping = {
                            'BLUE-GREEN': 'blueGreen',
                            'CANARY': 'canary',
                            'RECREATE': 'recreate',
                            'ROLLING': 'rolling'
                        }
                        
                        # Use mapped name if available, otherwise use lowercase template name
                        strategy_key = strategy_name_mapping.get(template_name, template_name.lower())
                        
                        if strategy_key in existing_strategy_details:
                            existing_details = existing_strategy_details[strategy_key]
                            # Compare using deepdiff via DevtronUtils
                            diff_result = self.DevtronUtils.compare_dicts(existing_details, config_strategy_details)
                            if diff_result.get("is_differ", False):
                                return True
                        else:
                            # Strategy key not found in existing strategy, they differ
                            return True
                    else:
                        # No deployment strategy in existing config, they differ
                        return True
                else:
                    # Strategy not found in existing strategies, they differ
                    return True
            
            # Check if any existing strategy is missing from config
            for template_name in existing_strategy_map:
                if template_name not in config_strategy_map:
                    return True
                    
            return False
        except Exception as e:
            print(f"Error comparing deployment strategies: {str(e)}")
            return True  # If we can't compare, assume they differ

    def _build_updated_strategies(self, existing_strategies: list, config_strategies: list, app_id: int) -> list:
        """
        Build updated strategies list by merging existing strategies with configured updates.
        
        Args:
            existing_strategies (list): Existing deployment strategies from the CD pipeline
            config_strategies (list): Configured deployment strategies from the YAML
            app_id (int): The application ID
            
        Returns:
            list: Updated strategies list
        """
        # Handle case where config_strategies is None or empty (deployment strategies removed)
        if config_strategies is None:
            # Follow the default strategy path similar to create-app command when strategies are explicitly removed
            strategies_result = self.get_deployment_strategies(app_id)
            if strategies_result['success']:
                api_strategies = strategies_result['strategies'].get('result', {}).get('pipelineStrategy', [])
                # Find the default strategy
                default_strategy = None
                for strategy in api_strategies:
                    if strategy.get('default', False):
                        default_strategy = strategy
                        break
                
                # If no default strategy found, use the first one
                if default_strategy is None and api_strategies:
                    default_strategy = api_strategies[0]
                # Convert to the format expected by the API
                if default_strategy:
                    strategies = [self._convert_strategy_format(default_strategy, is_default=True)]
                else:
                    # Fallback to hardcoded ROLLING strategy if API doesn't return any strategies
                    strategies = [self._get_default_rolling_strategy()]
            else:
                # Fallback to hardcoded ROLLING strategy if API call fails
                strategies = [self._get_default_rolling_strategy()]
            return strategies
        elif not config_strategies:
            # Empty list means no strategies should be used, but this should not happen in practice
            # as there should always be at least one strategy
            # Let's use the default strategy path in this case too
            strategies_result = self.get_deployment_strategies(app_id)
            if strategies_result['success']:
                api_strategies = strategies_result['strategies'].get('result', {}).get('pipelineStrategy', [])
                # Find the default strategy
                default_strategy = None
                for strategy in api_strategies:
                    if strategy.get('default', False):
                        default_strategy = strategy
                        break
                
                # If no default strategy found, use the first one
                if default_strategy is None and api_strategies:
                    default_strategy = api_strategies[0]
                # Convert to the format expected by the API
                if default_strategy:
                    strategies = [self._convert_strategy_format(default_strategy, is_default=True)]
                else:
                    # Fallback to hardcoded ROLLING strategy if API doesn't return any strategies
                    strategies = [self._get_default_rolling_strategy()]
            else:
                # Fallback to hardcoded ROLLING strategy if API call fails
                strategies = [self._get_default_rolling_strategy()]
            return strategies
        
        # Create a mapping of deployment template to strategy for config strategies
        config_strategy_map = {}
        for strategy in config_strategies:
            name = strategy.get("name")
            if name:
                config_strategy_map[name.upper()] = strategy
        
        updated_strategies = []
        
        # Process configured strategies using the existing _convert_user_strategy function
        for template_name, config_strategy in config_strategy_map.items():
            # Use the existing _convert_user_strategy function to properly convert the strategy
            try:
                converted_strategy = self._convert_user_strategy(config_strategy, app_id, config_strategy.get("default", False))
                updated_strategies.append(converted_strategy)
            except ValueError as e:
                # If we can't convert the strategy, try to update an existing one
                # Find the existing strategy with the same template name
                existing_strategy = None
                for strategy in existing_strategies:
                    if strategy.get("deploymentTemplate", "").upper() == template_name:
                        existing_strategy = strategy
                        break
                
                if existing_strategy:
                    updated_strategy = existing_strategy.copy()
                    
                    # Update the config section
                    config_strategy_details = config_strategy.get("strategy", {})
                    config = updated_strategy.get("config", {})
                    
                    if "deployment" in config and "strategy" in config["deployment"]:
                        # Use the same strategy key mapping as in _convert_user_strategy
                        strategy_name_mapping = {
                            'BLUE-GREEN': 'blueGreen',
                            'CANARY': 'canary',
                            'RECREATE': 'recreate',
                            'ROLLING': 'rolling'
                        }
                        
                        # Get the correct strategy key name
                        strategy_key = strategy_name_mapping.get(template_name, template_name.lower())
                        
                        if strategy_key in config["deployment"]["strategy"]:
                            # Update the strategy configuration with values from config
                            for key, value in config_strategy_details.items():
                                config["deployment"]["strategy"][strategy_key][key] = value
                            
                            updated_strategy["config"] = config
                            
                            # Update JSON and YAML strings
                            updated_strategy["jsonStr"] = json.dumps(config, indent=4)
                            updated_strategy["yamlStr"] = DevtronUtils.convert_dict_to_yaml(config)
                    
                    updated_strategies.append(updated_strategy)
                else:
                    # This is a new strategy that we couldn't convert, skip it
                    print(f"Warning: Could not create new strategy {template_name}: {e}")
                    continue
        
        # Ensure only one strategy is marked as default
        default_count = sum(1 for strategy in updated_strategies if strategy.get("default", False))
        if default_count > 1:
            # Keep the first one that was already default, or make the first one default if none was
            first_default_index = -1
            for i, strategy in enumerate(updated_strategies):
                if strategy.get("default", False):
                    if first_default_index == -1:
                        first_default_index = i
                    else:
                        strategy["default"] = False
        elif default_count == 0 and updated_strategies:
            # Make the first strategy default if none is marked as default
            updated_strategies[0]["default"] = True
            
        return updated_strategies



    def handle_cd_pipelines(self, base_url, headers, app_id, workflow, ci_pipeline_id, allow_deletion):
        import requests
        try:
            url = f"{base_url}/orchestrator/app/cd-pipeline/{app_id}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get CD Pipelines"
                }

            pipelines = response.json().get("result", {}).get("pipelines", [])
            cd_pipelines = workflow.get("cd_pipelines", [])
            result = self.DevtronUtils.get_wf_id_from_cd_id(self.base_url, self.headers,ci_pipeline_id, app_id)
            if not result["success"]:
                return {
                    "success": False,
                    "message": "Could not get workflow ID"
                }
            wf_id = result.get("wf_id")
            desired_cd_pipeline_config = {}

            for pipeline in cd_pipelines:
                desired_cd_pipeline_config[pipeline.get("environment_name")] = (pipeline.get("depends_on", "root"), pipeline)

            get_current_cd_pipeline_config = self.get_cd_pipeline_config(app_id, ci_pipeline_id)
            if not get_current_cd_pipeline_config["success"]:
                return {
                    "success": False,
                    "error": "Failed to get the cd pipeline conifg"
                }
            current_cd_pipeline_config = get_current_cd_pipeline_config["data"]

            pipelines_to_delete = []
            pipelines_to_update = []
            pipelines_to_create = []



            for key, value in current_cd_pipeline_config.items():
                if not desired_cd_pipeline_config.get(key, False):
                    pipelines_to_delete.append(value[1])
                else:
                    if value[0] != desired_cd_pipeline_config[key][0]:
                        pipelines_to_delete.append(value[1])
                    else:
                        pipelines_to_update.append((value[1], desired_cd_pipeline_config[key][1].get("environment_name")))

            for key, value in desired_cd_pipeline_config.items():
                if not current_cd_pipeline_config.get(key, False):
                    pipelines_to_create.append(value[1])
                else:
                    if value[0] != current_cd_pipeline_config[key][0]:
                        pipelines_to_create.append(value[1])


            # pipelines_to_delete = [
            #     pipeline.get("id", 0) for pipeline in pipelines
            #     if pipeline.get("environmentName", "") not in [cd_pipeline.get("environment_name", "") for cd_pipeline in cd_pipelines] and pipeline.get("ciPipelineId") == ci_pipeline_id
            # ]


            # pipelines_to_create = [
            #     cd_pipeline for cd_pipeline in cd_pipelines
            #     if cd_pipeline.get("environment_name", "") not in [pipeline.get("environmentName", "") for pipeline in pipelines]
            # ]


            # pipelines_to_update = [
            #     (pipeline.get("id", 0), pipeline.get("environmentName", "")) for pipeline in pipelines
            #     if pipeline.get("environmentName", "") in [cd_pipeline.get("environment_name", "") for cd_pipeline in cd_pipelines]
            # ]


            for pipeline_id in pipelines_to_delete:
                print(f"Deleting pipeline with ID:", pipeline_id)
                delete_pipeline_result = CdPipelineHandlers.delete_cd_pipeline(base_url, headers, app_id, pipeline_id, allow_deletion)
                if not delete_pipeline_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to delete a CD Pipeline with id {pipeline_id}"
                    }


            for pipeline in pipelines_to_update:
                print("Updating pipeline with ID:", pipeline)
                for cd_pipeline in workflow.get("cd_pipelines", []):
                    if cd_pipeline.get("environment_name", "") == pipeline[1]:
                        print("CD Pipeline to update:", cd_pipeline.get("name", ""))
                        updated_pipeline_result = CdPipelineHandlers.update_cd_pipeline(base_url, headers, app_id, pipeline[0], cd_pipeline)
                        if not updated_pipeline_result["success"]:
                            return {
                                "success": False,
                                "error": updated_pipeline_result["error"]
                            }
                        break

            if pipelines_to_create:
                create_pipeline_result = self.create_cd_pipelines_with_dependencies(app_id, wf_id, ci_pipeline_id, pipelines_to_create)
                if not create_pipeline_result["success"]:
                    return {
                        "success": False,
                        "error": "Failed to create pipeline"
                    }

            return {
                "success": True,
                "message": "Pipelines have been updated"
            }

        except Exception as e:
            print("Excception occurred in getting CD Pipeline")
            return {
                "success": False,
                "error": str(e)
            }

    def get_cd_pipeline_config(self, app_id, ci_pipeline_id) -> dict:
        try:
            current_cd_pipeline_config = {}
            url = f"{self.base_url}/orchestrator/app/cd-pipeline/{app_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get CD pipelines"
                }
            all_pipelines = response.json().get("result", {}).get("pipelines", [])
            pipelines = []
            if not all_pipelines:
                return current_cd_pipeline_config
            for pipeline in all_pipelines:
                if pipeline.get("ciPipelineId") == ci_pipeline_id:
                    pipelines.append(pipeline)
            for pipeline in pipelines:
                parent_type = pipeline.get("parentPipelineType")
                if parent_type != "CD_PIPELINE":
                    current_cd_pipeline_config[pipeline["environmentName"]] = ("root", pipeline["id"])
                else:
                    parent_id = pipeline.get("parentPipelineId", 0)
                    env = ""
                    for p in pipelines:
                        if p.get("id", 0) == parent_id:
                            env = p["environmentName"]
                            break
                    current_cd_pipeline_config[pipeline["environmentName"]] = (env, pipeline["id"])

            return {
                "success": True,
                "data": current_cd_pipeline_config
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }