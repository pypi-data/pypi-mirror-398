from tron.core.app.env_override_configurations.overrideDeploymentTemplate import EnvOverrideHandler
from tron.core.app.workflow.cd_pipeline.cd_pipeline_models import *
from tron.core.app.workflow.ci_pipeline.ci_pipeline_handler import *
from tron.utils import DevtronUtils

class CdPipelineHandlers:
    def __intit__(self):
        pass


    @staticmethod
    def delete_cd_pipeline(base_url: str, headers: dict, app_id: int, cd_pipeline_id: int, is_allow_deletion: bool = False) -> dict:
        import requests
        import json

        try:
            if not is_allow_deletion:
                print("Deleting CD pipeline will also delete the resources created by deployments in this environment, please add --allow-deletion to confirm deletion of this cd pipeline")

                return {
                    'success': False,
                    'error': "CD pipeline deletion is not allowed please use --allow-deletion flag"
                }
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

    @staticmethod
    def get_env_ns_details(base_url, headers, env):
        import  requests
        try:
            url = f"{base_url}/orchestrator/env/autocomplete"
            params = {
                "auth": "false",
                "showDeploymentOptions": "true"
            }
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get the env to namespace details"
                }
            result = response.json().get("result", [])
            for e in result:
                if e.get("environment_name") == env:
                    return {
                        "success": True,
                        "namespace": e.get("namespace")
                    }
            return {
                "success": False,
                "error": "Environment not found"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }



    @staticmethod
    def update_cd_pipeline(base_url: str, headers: dict, app_id: int, cd_pipeline_id: int, cd_config):
        try:
            environment_name = cd_config.get("environment_name")
            get_ns = CdPipelineHandlers.get_env_ns_details(base_url, headers, environment_name)
            if not get_ns["success"]:
                return {
                    "success": False,
                    "error": "Failed to get the ns details"
                }
            namespace = get_ns.get("namespace")
            environment_name = cd_config.get("environment_name", "")
            get_env_id = DevtronUtils.get_env_id(base_url, headers, environment_name)
            if not get_env_id["success"]:
                return {
                    "success": False,
                    "error": "Failed to get env_id"
                }
            env_id = get_env_id.get("environment_id")

            cd_pipeline = CdPipelineHandlers.get_cd_pipeline(base_url, headers, app_id, cd_pipeline_id)
            if not cd_pipeline["success"]:
                return {
                    "success": False,
                    "error": cd_pipeline["error"]
                }
            cd = cd_pipeline.get("cd_pipeline", None)
            if not cd:
                return {
                    "success": False,
                    "error": "CD Pipeline not found"
                }

            if cd_config.get("is_manual", False):
                cd.trigger_type = "MANUAL"
            else:
                cd.trigger_type = "AUTOMATIC"


            plugins = cd_config.get("pre_cd_configs", {}).get("tasks", []).copy()
            plugins.extend(cd_config.get("post_cd_configs", {}).get("tasks", []))



            applied_plugin_metadata = []

            if plugins:
                for plugin in plugins:
                    # Only process plugin types, skip custom types
                    plugin_type = plugin.get("type", "plugin").lower()
                    if plugin_type == "plugin":
                        plugin_name = plugin.get("name", "")
                        if not plugin_name:
                            continue
                        plugin_details_result = DevtronUtils.get_plugin_details_by_name(base_url, headers, plugin_name)
                        if not plugin_details_result["success"]:
                            return {
                                "success": False,
                                "error": f"Plugin '{plugin_name}' not found"
                            }
                        applied_plugin_metadata.append(plugin_details_result.get("plugin", ""))

            pipeline_plugin_ids = CdPipelineHandlers.get_pre_post_deploy_plugin_ids(cd)
            plugin_metadata = {}
            if pipeline_plugin_ids:
                plugin_metadata_response = DevtronUtils.get_plugin_details_by_id(base_url, headers, pipeline_plugin_ids, app_id)
                if not plugin_metadata_response["success"]:
                    return {
                        "success": False,
                        "message": "Plugin metadata not found"
                    }
                plugin_metadata = plugin_metadata_response.get("plugin_data", {})
                
            updated_pre_cd_configs = CiPipelineHandlers.update_pre_post_build_config(
                cd.pre_deploy_stage,
                cd_config.get("pre_cd_configs", {}).get("tasks", []),
                plugin_metadata,
                applied_plugin_metadata,
                True,
                "PRE_CD",
                "MANUAL" if cd_config.get("pre_cd_configs", {}).get("is_manual", False) else "AUTOMATIC"
            )

            updated_post_cd_configs = CiPipelineHandlers.update_pre_post_build_config(
                cd.post_deploy_stage,
                cd_config.get("post_cd_configs", {}).get("tasks", []),
                plugin_metadata,
                applied_plugin_metadata,
                True,
                "POST_CD",
                "MANUAL" if cd_config.get("post_cd_configs", {}).get("is_manual", False) else "AUTOMATIC"
            )


            cd.pre_deploy_stage = updated_pre_cd_configs
            cd.post_deploy_stage = updated_post_cd_configs

            # Map run_in_app_env flags from config (only supported for pre_cd and post_cd)
            cd.run_pre_stage_in_env = bool(cd_config.get('pre_cd_configs', {}).get('run_in_app_env', False))
            cd.run_post_stage_in_env = bool(cd_config.get('post_cd_configs', {}).get('run_in_app_env', False))

            patch_cd_result = CdPipelineHandlers.patch_cd_pipeline(base_url, headers, cd, namespace)

            if not patch_cd_result["success"]:
                print("Failed to patch CD Pipeline")
                return {
                    "success": False,
                    "error": patch_cd_result["error"]
                }
            print("CD Pipeline updated successfully")

            handle_env_override_result = EnvOverrideHandler.handle_env_override(base_url, headers, app_id, cd_config, environment_name, env_id, namespace)
            if not handle_env_override_result["success"]:
                print("Env override patch failed")
                return {
                    "success": False,
                    "error": handle_env_override_result["error"]
                }
            return {
                "success": True,
                "message": "CD Pipeline updated"
            }

        except Exception as e:
            print("Excception occurred in updating CD Pipeline", e)
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def patch_cd_pipeline(base_url, headers, cd_pipeline: CdPipeline, namespace: str):
        import requests, json
        try:

            if cd_pipeline.pre_deploy_stage:

                pre_deploy = cd_pipeline.pre_deploy_stage.to_dict()
            else:
                pre_deploy = {}
            if cd_pipeline.post_deploy_stage:
                post_deploy = cd_pipeline.post_deploy_stage.to_dict()
            else:
                post_deploy = {}

            url = f"{base_url}/orchestrator/app/cd-pipeline/patch"

            payload = {
                "appId": cd_pipeline.app_id,
                "pipeline": {
                    "name": cd_pipeline.name,
                    "ciPipelineId": cd_pipeline.ci_pipeline_id,
                    "environmentId": cd_pipeline.environment_id,
                    "namespace": namespace,
                    "id": cd_pipeline.id,
                    "strategies": cd_pipeline.strategies,
                    "parentPipelineType": cd_pipeline.parent_pipeline_type,
                    "parentPipelineId": cd_pipeline.parent_pipeline_id,
                    "isClusterCdActive": cd_pipeline.is_cluster_cd_active,
                    "deploymentAppType": cd_pipeline.deployment_app_type,
                    "deploymentAppName": cd_pipeline.deployment_app_name,
                    "releaseMode": cd_pipeline.release_mode,
                    "deploymentAppCreated": cd_pipeline.deployment_app_created,
                    "triggerType": cd_pipeline.trigger_type,
                    "environmentName": cd_pipeline.environment_name,
                    "preStageConfigMapSecretNames": cd_pipeline.pre_stage_config_map_secret_names.to_dict(),
                    "postStageConfigMapSecretNames": cd_pipeline.post_stage_config_map_secret_names.to_dict(),
                    "containerRegistryName": cd_pipeline.container_registry_name,
                    "repoName": cd_pipeline.repo_name,
                    "manifestStorageType": cd_pipeline.manifest_storage_type,
                    "runPreStageInEnv": getattr(cd_pipeline, 'run_pre_stage_in_env', False),
                    "runPostStageInEnv": getattr(cd_pipeline, 'run_post_stage_in_env', False),
                    "preDeployStage": pre_deploy,
                    "postDeployStage": post_deploy,
                    "customTag": cd_pipeline.custom_tag,
                    "enableCustomTag": cd_pipeline.enable_custom_tag,
                    "customTagStage": cd_pipeline.custom_tag_stage,
                    "isDigestEnforcedForPipeline": cd_pipeline.is_digest_enforced_for_pipeline,
                    "isDigestEnforcedForEnv": cd_pipeline.is_digest_enforced_for_env,
                    "addType": cd_pipeline.add_type
                },
                "action": 2
            }


            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code != 200:
                print("Exception occurred could not patch the CD Pipeline")
                return {
                    "success": False,
                    "error": "Could not patch the CD Pipeline"
                }
            print("Updated the pipeline successfully")

            return {
                "success": True,
                "message": "Updated the pipeline successfully"
            }
        except Exception as e:
            print("Excception occurred in patching CD Pipeline", e)




    @staticmethod
    def get_cd_pipeline(base_url: str, headers: dict, app_id: int, cd_pipeline_id: int):
        import requests

        url = f"{base_url}/orchestrator/app/v2/cd-pipeline/{app_id}/{cd_pipeline_id}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                print("Exception occurred could not get the CD pipeline details")
                return {
                    "success": False,
                    "error": "Could not get the CD pipeline details"
                }
            details = response.json().get("result", {})


            pre_deploy_stage = CiPipelineHandlers.get_pre_post_build_config(details.get("preDeployStage", {}))
            post_deploy_stage = CiPipelineHandlers.get_pre_post_build_config(details.get("postDeployStage", {}))

            cd_pipeline = CdPipeline(
                _id=details.get("id"),
                environment_id=details.get("environmentId"),
                environment_name=details.get("environmentName"),
                description=details.get("description"),
                ci_pipeline_id=details.get("ciPipelineId"),
                trigger_type=details.get("triggerType"),
                name=details.get("name"),
                strategies=details.get("strategies"),
                deployment_template=details.get("deploymentTemplate"),
                pre_stage=PrePostStage(),
                post_stage=PrePostStage(),
                pre_stage_config_map_secret_names=PrePostStageConfigMapSecretNames(),
                post_stage_config_map_secret_names=PrePostStageConfigMapSecretNames(),
                is_cluster_cd_active=details.get("isClusterCdActive"),
                parent_pipeline_id=details.get("parentPipelineId"),
                parent_pipeline_type=details.get("parentPipelineType"),
                deployment_app_type=details.get("deploymentAppType"),
                user_approval_config=details.get("userApprovalConfig"),
                approval_config_data=details.get("approvalConfigData"),
                app_name=details.get("appName"),
                deployment_app_delete_request=details.get("deploymentAppDeleteRequest"),
                deployment_app_created=details.get("deploymentAppCreated"),
                app_id=details.get("appId"),
                is_virtual_environment=details.get("isVirtualEnvironment"),
                helm_package_name=details.get("helmPackageName"),
                chart_name=details.get("chartName"),
                chart_base_version=details.get("chartBaseVersion"),
                container_registry_name=details.get("containerRegistryName"),
                repo_name=details.get("repoName"),
                manifest_storage_type=details.get("manifestStorageType"),
                pre_deploy_stage=pre_deploy_stage,
                post_deploy_stage=post_deploy_stage,
                custom_tag=details.get("customTag"),
                custom_tag_stage=details.get("customTagStage"),
                enable_custom_tag=details.get("enableCustomTag"),
                is_prod_env=details.get("isProdEnv"),
                is_git_ops_repo_not_configured=details.get("isGitOpsRepoNotConfigured"),
                switch_from_ci_pipeline_id=details.get("switchFromCiPipelineId"),
                add_type=details.get("addType"),
                child_pipeline_id=details.get("childPipelineId"),
                is_digest_enforced_for_pipeline=details.get("isDigestEnforcedForPipeline"),
                is_digest_enforced_for_env=details.get("isDigestEnforcedForEnv"),
                application_object_cluster_id=details.get("applicationObjectClusterId"),
                application_object_namespace=details.get("applicationObjectNamespace"),
                deployment_app_name=details.get("deploymentAppName"),
                release_mode=details.get("releaseMode"),
                trigger_blocked_info=details.get("triggerBlockedInfo"),
                is_trigger_blocked=details.get("isTriggerBlocked"),
                is_custom_chart=details.get("isCustomChart"),
            )

            return {
                "success": True,
                "cd_pipeline": cd_pipeline
            }

        except Exception as e:
            print("Excception occurred in getting CD-Pipeline", str(e))

            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_pre_post_deploy_plugin_ids(cd_pipeline: CdPipeline) -> list:
        plugin_ids = []
        if cd_pipeline.pre_deploy_stage:
            for step in cd_pipeline.pre_deploy_stage.steps:
                # Only collect plugin IDs for REF_PLUGIN steps, skip INLINE/custom steps
                if step.step_type == "REF_PLUGIN" and step.plugin_ref_step_detail:
                    plugin_ids.append(step.plugin_ref_step_detail.plugin_id)
        if cd_pipeline.post_deploy_stage:
            for step in cd_pipeline.post_deploy_stage.steps:
                # Only collect plugin IDs for REF_PLUGIN steps, skip INLINE/custom steps
                if step.step_type == "REF_PLUGIN" and step.plugin_ref_step_detail:
                    plugin_ids.append(step.plugin_ref_step_detail.plugin_id)

        return plugin_ids
