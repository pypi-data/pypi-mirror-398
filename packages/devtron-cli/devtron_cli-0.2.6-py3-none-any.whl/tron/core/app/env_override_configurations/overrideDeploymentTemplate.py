import base64

import requests
from .envConfigMapSecret import DevtronOverrideConfigMapSecret
from tron.core.app.env_override_configurations import env_override_handler as eoh


class EnvOverrideHandler:


    @staticmethod
    def config_id_by_chart_ref_id(base_url, headers, app_id, env_id, chart_ref_id):
        try:
            url = f"{base_url}/orchestrator/app/env/{app_id}/{env_id}/{chart_ref_id}"
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get config id"

                }
            result = response.json().get("result", {})
            config_id = result.get("environmentConfig", {}).get("id", 0)
            if config_id == 0:
                return {
                    "success": True,
                    "config_id": 0
                }
            elif not config_id:
                return {
                    "success": False,
                    "error": "Failed to get config id"
                }
            return {
                "success": True,
                "config_id": config_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def reset_env_override_template(base_url, headers, app_id, env_id, config_id):
        try:
            url = f"{base_url}/orchestrator/app/env/reset/{app_id}/{env_id}/{config_id}"
            response = requests.delete(url, headers=headers)

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to reset env override"
                }
            return {
                "success": True,
                "message": "Env override reset successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    @staticmethod
    def reset_config_override(base_url, headers, app_id, env_id, config_type):
        try:
            get_configs = eoh.get_cm_cs_for_env(base_url, headers, app_id, env_id)
            if not get_configs["success"]:
                return {
                    "success": False,
                    "error": get_configs["error"]
                }
            configs = get_configs.get("result", {}).get("resourceConfig", [])
            configs_to_reset = []
            for config in configs:
                if config.get("id", 0) != 0 and config.get("type", "") == config_type:
                    configs_to_reset.append((config.get("id", 0), config.get("name", ""), config.get("type", "")))



            check_approval_result = eoh.get_approval_data(base_url, headers, app_id)
            if not check_approval_result["success"]:
                return {
                    "success": False,
                    "error": check_approval_result["error"]
                }

            protect_config = None
            for res in check_approval_result["result"]:
                if res["envId"] == env_id:
                    protect_config = res["approvalConfigurations"]
                    break
            if protect_config:
                if config_type == "ConfigMap":
                    if "configuration/config-map" in [itr.get("kind", "") for itr in protect_config]:

                        for config_id, config_name, config_type in configs_to_reset:
                            reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type, is_protected=True)
                            if not reset_config["success"]:
                                return {
                                    "success": False,
                                    "error": reset_config["error"]
                                }

                        print(f"Successfully reset the {config_type}s")
                        return {
                            "success": True,
                            "message": "Successfully reset the CM/CS"
                        }
                elif config_type == "Secret":

                    if "configuration/config-secret" in [itr.get("kind", "") for itr in protect_config]:

                        for config_id, config_name, config_type in configs_to_reset:

                            reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type, is_protected=True)
                            if not reset_config["success"]:
                                return {
                                    "success": False,
                                    "error": reset_config["error"]
                                }

                        print(f"Successfully reset the {config_type}s")
                        return {
                            "success": True,
                            "message": "Successfully reset the CM/CS"
                        }
            else:

                for config_id, config_name, config_type in configs_to_reset:

                    reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type)
                    if not reset_config["success"]:
                        return {
                            "success": False,
                            "error": reset_config["error"]
                        }

                print(f"Successfully reset the {config_type}s")
                return {
                    "success": True,
                    "message": "Successfully reset the CM/CS"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def encode_values_to_base64(data: dict) -> dict:

        encoded_data = {}
        for key, value in data.items():
            value_str = str(value)
            encoded_value = base64.b64encode(value_str.encode("utf-8")).decode("utf-8")
            encoded_data[key] = encoded_value
        return encoded_data

    @staticmethod
    def patch_cm_cs(base_url, headers, app_id: int, environment_id: int, config_type: str, cm_cs_data: dict) -> dict:
        import yaml, os,json
        try:
            api_url = f"{base_url.rstrip('/')}/orchestrator/config/environment/{config_type}"
            cm_cs_name      = cm_cs_data.get("name", "")
            cm_cs_type      = cm_cs_data.get("type", "environment")
            is_external     = cm_cs_data.get("external", False)
            from_file       = cm_cs_data.get("from_file", "")
            config_data     = cm_cs_data.get("data", {})
            mount_path      = cm_cs_data.get("mountPath", None)
            subpath         = cm_cs_data.get("subPath", None)
            file_permission = cm_cs_data.get("filePermission", None)
            merge_strategy  = cm_cs_data.get("merge_strategy", None)
            role_arn        = cm_cs_data.get("roleARN", "")
            external_type   = cm_cs_data.get("externalType", "")
            eso_secret_data = cm_cs_data.get("esoSecretData", None)
            eso_subpath     = cm_cs_data.get("esoSubPath", None)
            if from_file:
                if not os.path.isfile(from_file):
                    return {'success': False, 'error': f"File not found: {from_file}"}
                with open(from_file, 'r') as f:
                        config_data = yaml.safe_load(f)
            if config_type == "cs":
                config_data = EnvOverrideHandler.encode_values_to_base64(config_data)
            cm_cs_payload = EnvOverrideHandler.build_cm_cs_payload(app_id, environment_id, cm_cs_name, cm_cs_type, is_external, config_data, role_arn, external_type, eso_secret_data, mount_path, subpath, file_permission, eso_subpath, merge_strategy)
            response = requests.post(api_url, headers=headers, data=json.dumps(cm_cs_payload))
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print("Successfully patched ConfigMap/Secret override")
                    return {'success': True, 'message': 'ConfigMap/Secret override patched successfully'}
                else:
                    return {'success': False, 'error': f"Failed to patch ConfigMap/Secret override: {result.get('error', 'Unknown error')}"}
            else:
                return {'success': False, 'error': f"Failed to patch ConfigMap/Secret override: {response.text}"}

        except Exception as e:
            return {'success': False, 'error': str(e)}


    @staticmethod
    def build_cm_cs_payload(
        app_id: int,
        environment_id: int,
        cm_cs_name: str,
        cm_cs_type: str,
        is_external: bool,
        config_data: dict,
        role_arn: str,
        external_type: str,
        eso_secret_data: dict,
        mount_path: str,
        subpath: bool,
        file_permission: str,
        eso_subpath: str,
        merge_strategy: str
    ) -> dict:
        return {
            "appId": app_id,
            "environmentId": environment_id,
            "configData": [
                {
                    "name": cm_cs_name,
                    "type": cm_cs_type,
                    "external": is_external,
                    "data": config_data,
                    "roleARN": role_arn,
                    "externalType": external_type,
                    "esoSecretData": eso_secret_data,
                    "mountPath": mount_path,
                    "subPath": subpath,
                    "filePermission": file_permission,
                    "esoSubPath": eso_subpath,
                    "mergeStrategy": merge_strategy
                }
            ],
            "isExpressEdit": False
        }

    @staticmethod
    def handle_configs(base_url, headers, app_id, configs_to_create, config_type, env_id):
        import os, yaml
        for config_map in configs_to_create:
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
                    cm_secret_handler = DevtronConfigMapSecret(base_url, headers)
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
                    print("Exception occurred while fetching base config")
                    return {
                        "success": False,
                        "error": "Exception occurred while fetching base config"

                    }

            # Check if the config map exists at the base level
            try:
                from tron.core.app.base_configurations.configMapSecret import DevtronConfigMapSecret
                cm_secret_handler = DevtronConfigMapSecret(base_url, headers)
                base_config_details = cm_secret_handler.get_config_map_details(app_id, config_map.get("name"))
                if not base_config_details.get("success"):
                    # If it doesn't exist at base, it's environment-level only
                    if "merge_strategy" in config_map:
                        del config_map["merge_strategy"]
            except Exception:
                # If there's an error checking, assume it doesn't exist at base
                if "merge_strategy" in config_map:
                    del config_map["merge_strategy"]
                print("Exception occurred while checking base config")
                return {
                    "success": False,
                    "error": "Exception occurred while checking base config"
                }

            if config_type == "ConfigMap":
                config_type_short = "cm"
            elif config_type == "Secret":
                config_type_short = "cs"
            else:
                return {
                    "success": False,
                    "error": "Confgtype error"
                }

            patch_override_config = EnvOverrideHandler.patch_cm_cs(base_url, headers, app_id, env_id, config_type_short, config_map)
            if not patch_override_config.get("success", True):
                return {
                    'success': False,
                    'error': "The pipeline has been created but could not patch the override config map"
                }

            print(f"Successfully patched override config map for environment {env_id}")
        return {
            "success": True,
            "message": "Successfully patched override configs"
        }



    @staticmethod
    def create_base_cm_cs_draft_p(base_url, headers, app_id, env_id, resource_type, resource_name, action, cm_cs_data, user_comment=""):
        import json

        try:

            url = f"{base_url}/orchestrator/draft"
            data = {
                "id": 0,
                "appId": int(app_id),
                "configData": [cm_cs_data]
            }

            final_data = json.dumps(data, separators=(",", ":"), default=str, ensure_ascii=False)
            payload = {
                "appId": int(app_id),
                "envId": int(env_id),
                "resource": int(resource_type),
                "resourceName": resource_name,
                "action": int(action),
                "data": final_data,
                "userComment": user_comment,
                "changeProposed": True,
                "protectNotificationConfig": {"emailIds": []}
            }


            headers = dict(headers)
            headers['Content-Type'] = 'text/plain;charset=UTF-8'

            # Convert payload to JSON string for proper HTTP request
            json_payload = json.dumps(payload, separators=(",", ":"), default=str, ensure_ascii=False)
            response = requests.post(url, headers=headers, data=json_payload.encode('utf-8'))

            try:
                response_json = response.json()
                if response.status_code == 200:
                    result = response_json.get('result', {})
                    return {'success': True, 'result': result}
                else:
                    error_msg = response_json.get('errors', [{}])[0].get('userMessage', response.text)
                    return {'success': False, 'error': f'API request failed: {error_msg}'}

            except json.JSONDecodeError:
                if response.status_code == 200:
                    return {'success': True, 'result': {}, 'raw_response': response.text}
                else:
                    return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}


    @staticmethod
    def handle_secrets_protected(base_url, headers, app_id, configs_to_create, env_id):

        for secret_data in configs_to_create:

            try:

                # Ensure all supported fields are present in secret_data
                secret_data_full = dict(secret_data)
                for key, default in [
                    ("name", None),
                    ("type", "environment"),
                    ("external", False),
                    ("data", {}),
                    ("roleARN", None),
                    ("externalType", None),
                    ("esoSecretData", None),
                    ("mountPath", None),
                    ("subPath", None),
                    ("filePermission", None),
                    ("esoSubPath", None),
                    ("mergeStrategy", None),
                ]:
                    if key not in secret_data_full:
                        secret_data_full[key] = default

                # Set default externalType to 'KubernetesSecret' if external is True and externalType is not specified
                if secret_data_full.get("external") is True and secret_data_full.get("externalType") is None:
                    secret_data_full["externalType"] = "KubernetesSecret"
                # If mountPath is present and not empty, set type to 'volume'
                if secret_data_full.get("mountPath"):
                    secret_data_full["type"] = "volume"

                # Handle special case for external secrets with mountPath and subPath
                if (secret_data_full.get("external") is True and
                        secret_data_full.get("mountPath") and
                        secret_data_full.get("subPath")):

                    sub_path_value = secret_data_full["subPath"]
                    # subPath cannot be boolean or string "true"/"false", must be a string other than true/false
                    if (sub_path_value is True or sub_path_value is False or
                            str(sub_path_value).lower() in ["true", "false"]):
                        return {
                            'success': False,
                            'error': 'subPath cannot be "true"/"false" when external is true and mountPath is specified'
                        }

                    # Add subPath value to data field with empty string value
                    if "data" not in secret_data_full:
                        secret_data_full["data"] = {}
                    secret_data_full["data"][sub_path_value] = ""
                    # Set subPath to true as expected in API
                    secret_data_full['subPath'] = True

                print("Config approval is enabled for secrets. Creating draft instead of direct creation.")
                approval_config_update_result = EnvOverrideHandler.create_base_cm_cs_draft_p(base_url, headers, app_id, env_id=env_id, resource_type=2, resource_name=secret_data.get('name'), action=1, cm_cs_data=secret_data_full, user_comment="Creating/Updating base config map with config approval.")
                if not approval_config_update_result['success']:
                    return {'success': False, 'error': f"Failed to create/update draft: {approval_config_update_result['error']}"}
                return {'success': True, 'result': approval_config_update_result}
            except Exception as e:
                return {'success': False, 'error': f'Exception occurred: {str(e)}'}

        return {
            "success": True
        }


    @staticmethod
    def handle_configs_protected(base_url, headers, app_id, configs_to_create, config_type, env_id):

        for config_map_data in configs_to_create:
            try:

                # Ensure all supported fields are present in config_map_data
                config_map_data_full = dict(config_map_data)
                for key, default in [
                    ("name", None),
                    ("type", "environment"),
                    ("external", False),
                    ("data", {}),
                    ("roleARN", None),
                    ("externalType", None),
                    ("esoSecretData", None),
                    ("mountPath", None),
                    ("subPath", None),
                    ("filePermission", None),
                    ("esoSubPath", None),
                    ("mergeStrategy", None),
                ]:
                    if key not in config_map_data_full:
                        config_map_data_full[key] = default

                if config_map_data_full.get("mountPath"):
                    config_map_data_full["type"] = "volume"

                # Handle special case for external config maps with mountPath and subPath
                if (config_map_data_full.get("external") is True and
                        config_map_data_full.get("mountPath") and
                        config_map_data_full.get("subPath")):

                    sub_path_value = config_map_data_full["subPath"]
                    # subPath cannot be boolean or string "true"/"false", must be a string other than true/false
                    if (sub_path_value is True or sub_path_value is False or
                            str(sub_path_value).lower() in ["true", "false"]):
                        return {
                            'success': False,
                            'error': 'subPath cannot be "true"/"false" when external is true and mountPath is specified'
                        }

                    # Add subPath value to data field with empty string value
                    if "data" not in config_map_data_full:
                        config_map_data_full["data"] = {}
                    config_map_data_full["data"][sub_path_value] = ""
                    # Set subPath to true as expected in API
                    config_map_data_full['subPath'] = True


                print("Config approval is enabled for base config map. Creating draft instead of direct creation.")
                approval_config_update_result = EnvOverrideHandler.create_base_cm_cs_draft_p(base_url, headers, app_id, env_id=env_id, resource_type=1, resource_name=config_map_data.get('name'), action=1, cm_cs_data=config_map_data_full, user_comment="Creating/Updating base config map with config approval.")
                if not approval_config_update_result['success']:
                    return {'success': False, 'error': f"Failed to create/update draft: {approval_config_update_result['error']}"}
                return {'success': True, 'result': approval_config_update_result}

            except Exception as e:
                return {'success': False, 'error': f'Exception occurred: {str(e)}'}
        return {
            'success': True
        }

    @staticmethod
    def handle_config_override(base_url, headers, app_id, env_id, config_type, desired_configs):

        try:
            get_configs = eoh.get_cm_cs_for_env(base_url, headers, app_id, env_id)
            if not get_configs["success"]:
                return {
                    "success": False,
                    "error": get_configs["error"]
                }
            configs = get_configs.get("result", {}).get("resourceConfig", [])
            configs_to_reset = []
            for config in configs:
                if config.get("name", "") not in [desired_config.get("name", "") for desired_config in desired_configs]:
                    if config.get("id", 0) != 0 and config.get("type", "") == config_type:
                        configs_to_reset.append((config.get("id", 0), config.get("name", ""), config.get("type", "")))

            configs_to_update = []
            for cf in desired_configs:
                if cf.get("name", "") in [conf.get("name", "") for conf in configs]:
                    configs_to_update.append(cf)
            configs_to_create = []
            for cf in desired_configs:
                if cf.get("name", "") not in [conf.get("name", "") for conf in configs]:
                    configs_to_create.append(cf)

            check_approval_result = eoh.get_approval_data(base_url, headers, app_id)
            if not check_approval_result["success"]:
                return {
                    "success": False,
                    "error": check_approval_result["error"]
                }

            protect_config = None
            for res in check_approval_result["result"]:
                if res["envId"] == env_id:
                    protect_config = res["approvalConfigurations"]
                    break
            if not protect_config:

                for config_id, config_name, conf_type in configs_to_reset:
                    reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, conf_type)
                    if not reset_config["success"]:
                        return {
                            "success": False,
                            "error": reset_config["error"]
                        }

                handle_create = EnvOverrideHandler.handle_configs(base_url, headers, app_id, configs_to_create, config_type, env_id)
                if not handle_create["success"]:
                    return {
                        "success": False,
                        "error": handle_create["error"]
                    }
                handle_update = EnvOverrideHandler.handle_configs(base_url, headers, app_id, configs_to_update,config_type, env_id)
                if not handle_update["success"]:
                    return {
                        "success": False,
                        "error": handle_update["error"]
                    }
                print(f"Successfully patched override config map for environment {env_id}")

                return {
                    "success": True,
                    "message": "Successfully patched override configs"
                }
            else:
                if config_type == "ConfigMap":
                    if "configuration/config-map" in [itr.get("kind", "") for itr in protect_config]:

                        for config_id, config_name, config_type in configs_to_reset:
                            reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type, is_protected=True)
                            if not reset_config["success"]:
                                return {
                                    "success": False,
                                    "error": reset_config["error"]
                                }

                        print(f"Successfully reset the {config_type}s")
                    handle_create = EnvOverrideHandler.handle_configs_protected(base_url, headers, app_id, configs_to_create, config_type, env_id)
                    if not handle_create["success"]:
                        return {
                            "success": False,
                            "error": handle_create["error"]
                        }
                    handle_update = EnvOverrideHandler.handle_configs_protected(base_url, headers, app_id, configs_to_update, config_type, env_id)
                    if not handle_update["success"]:
                        return {
                            "success": False,
                            "error": handle_update["error"]
                        }
                    print(f"Successfully patched override config map for environment {env_id}")

                elif config_type == "Secret":

                    if "configuration/config-secret" in [itr.get("kind", "") for itr in protect_config]:

                        for config_id, config_name, config_type in configs_to_reset:

                            reset_config = eoh.reset_config(base_url, headers, app_id, env_id, config_id, config_name, config_type, is_protected=True)
                            if not reset_config["success"]:
                                return {
                                    "success": False,
                                    "error": reset_config["error"]
                                }

                        print(f"Successfully reset the {config_type}s")
                    handle_create = EnvOverrideHandler.handle_secrets_protected(base_url, headers, app_id, configs_to_create,  env_id)
                    if not handle_create["success"]:
                        return {
                            "success": False,
                            "error": handle_create["error"]
                        }
                    handle_update = EnvOverrideHandler.handle_secrets_protected(base_url, headers, app_id, configs_to_update,  env_id)
                    if not handle_update["success"]:
                        return {
                            "success": False,
                            "error": handle_update["error"]
                        }
                    print(f"Successfully patched override config-secrets for environment {env_id}")





        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def handle_env_override(base_url, headers, app_id, cd_config, environment_name, env_id, namespace):
        try:
            env_configuration = cd_config.get("env_configuration", None)
            get_chart_ref_id = OverrideDeploymentTemplateHandler.get_chart_ref_id_for_env(base_url, headers, app_id, env_id)
            if not get_chart_ref_id["success"]:
                return {
                    "success": False,
                    "error": get_chart_ref_id["error"]
                }
            chart_ref_id = get_chart_ref_id.get("chart_ref_id", 0)
            if not env_configuration:
                print("Deployment template not found, Removing the deployment template override.")

                get_config_id = EnvOverrideHandler.config_id_by_chart_ref_id(base_url, headers, app_id, env_id, chart_ref_id)
                if not get_config_id["success"]:
                    return {
                        "success": False,
                        "error": get_config_id["error"]
                    }
                config_id = get_config_id.get("config_id")
                if config_id == 0:
                    pass
                else:
                    reset_env_override = EnvOverrideHandler.reset_env_override_template(base_url, headers, app_id, env_id, config_id)
                    if not reset_env_override["success"]:
                        return {
                            "success": False,
                            "error": reset_env_override["error"]
                        }
                reset_configmaps = EnvOverrideHandler.reset_config_override(base_url, headers, app_id, env_id, "ConfigMap")
                if not reset_configmaps["success"]:
                    return {
                        "success": False,
                        "error": reset_configmaps["error"]
                    }
                reset_secrets = EnvOverrideHandler.reset_config_override(base_url, headers, app_id, env_id, "Secret")
                if not reset_secrets["success"]:
                    return {
                        "success": False,
                        "error": reset_secrets["error"]
                    }
                return {
                    "success": True,
                    "message": "Env Override updated successfully"
                }

            else:
                deployment_template = env_configuration.get("deployment_template", None)
                configmaps = env_configuration.get("config_maps", [])
                secrets = env_configuration.get("secrets", [])
                if not deployment_template:

                    print("Deployment template not found, Removing the deployment template override.")

                    get_config_id = EnvOverrideHandler.config_id_by_chart_ref_id(base_url, headers, app_id, env_id, chart_ref_id)
                    if not get_config_id["success"]:
                        return {
                            "success": False,
                            "error": get_config_id["error"]
                        }
                    config_id = get_config_id.get("config_id")
                    if config_id == 0:
                        pass
                    else:
                        reset_env_override = EnvOverrideHandler.reset_env_override_template(base_url, headers, app_id, env_id, config_id)
                        if not reset_env_override["success"]:
                            return {
                                "success": False,
                                "error": reset_env_override["error"]
                            }
                else:

                    patch_overriden_deployment_template = EnvOverrideHandler.patch_overriden_deployment_template(base_url, headers, app_id, env_id, deployment_template, chart_ref_id, environment_name, namespace)
                    if not patch_overriden_deployment_template["success"]:
                        return {
                            "success": False,
                            "error": f"Failed to patch the deployment template for the env: {environment_name}"
                        }
                if not configmaps:
                    print("configmaps not found in config file, inheriting from base")
                    reset_configmaps = EnvOverrideHandler.reset_config_override(base_url, headers, app_id, env_id, "ConfigMap")
                    if not reset_configmaps["success"]:
                        return {
                            "success": False,
                            "error": reset_configmaps["error"]
                        }
                else:
                    print("Updating the Configmaps")
                    config_handler = EnvOverrideHandler.handle_config_override(base_url, headers, app_id, env_id, "ConfigMap", configmaps)
                    if not config_handler["success"]:
                        return {
                            "success": False,
                            "error": config_handler["error"]
                        }
                if not secrets:
                    print("secrets not found in config file, inheriting from base")
                    reset_secrets = EnvOverrideHandler.reset_config_override(base_url, headers, app_id, env_id, "Secret")
                    if not reset_secrets["success"]:
                        return {
                            "success": False,
                            "error": reset_secrets["error"]
                        }
                else:
                    print("Updating the Secrets")
                    secret_handler = EnvOverrideHandler.handle_config_override(base_url, headers, app_id, env_id, "Secret", secrets)
                    if not secret_handler["success"]:
                        return {
                            "success": False,
                            "error": secret_handler["error"]
                        }
                return {
                    "success": True,
                    "message": "Env Override updated successfully"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


    @staticmethod
    def get_current_deployment_template(base_url: str, headers: dict, app_id: int, env_id: int, chart_ref_id: int) -> dict:
        get_current_config = eoh.template_config_handler(base_url, headers, app_id, env_id, chart_ref_id)
        if not get_current_config["success"]:
            return { "success": False, "error": get_current_config["error"] }
        return { "success": True, "result": get_current_config["result"] }


    @staticmethod
    def patch_overriden_deployment_template(base_url, headers, app_id, env_id, deployment_template, chart_ref_id, environment_name, namespace):
        import os, yaml
        try:

            get_current_deployment_template = EnvOverrideHandler.get_current_deployment_template(base_url, headers, app_id, env_id, chart_ref_id)
            if not get_current_deployment_template["success"]:
                return {
                    "success": False,
                    "error": get_current_deployment_template["error"]
                }
            current_deployment_template = get_current_deployment_template["result"]
            app_metrics = deployment_template.get("show_application_metrics", False)
            merge_strategy = deployment_template.get("merge_strategy", "patch")
            values_path = deployment_template.get("values_path", None)
            values_patch = deployment_template.get("values_patch", None)
            if values_path:
                if not os.path.isfile(values_path):
                    return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                with open(values_path, 'r') as f:
                    override_data = yaml.safe_load(f)
            else:
                override_data = values_patch
            id = current_deployment_template.get("environmentConfig", {}).get("id", 0)

            patch_template = eoh.template_patch_handler(base_url, headers, override_data, environment_name, env_id, chart_ref_id, app_metrics, id, merge_strategy, namespace)
            if not patch_template["success"]:
                return {
                    "success": False,
                    "error": patch_template["error"]
                }
            return {
                "success": True,
                "message": "Deployment template updated successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class OverrideDeploymentTemplateHandler:
    def __init__(self, base_url, headers):
        self.base_url                    = base_url
        self.headers                     = headers
        self.env_override_cm_cs          = DevtronOverrideConfigMapSecret(base_url,headers)

    @staticmethod
    def get_chart_ref_id_for_env(base_url, headers, app_id, env_id) -> dict:

        try:
            url = f"{base_url}/orchestrator/chartref/autocomplete/{app_id}/{env_id}"
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json().get('result', {})
                return {'success': True, 'chart_ref_id': result.get('latestEnvChartRef')}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_env_configuration_template(self,app_id,env_id,chart_ref_id) -> dict:
        """
        Fetch the override deployment template for a given app_id env_id and chart_ref_id from Devtron.
        Args:
            app_id (int or str): The application ID
            env_id (int or str): The environment ID
            chart_ref_id (int or str): The chartRef ID
        Returns:
            dict: {success: bool, env_configuration_template: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/app/env/{app_id}/{env_id}/{chart_ref_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json().get('result', {})
                return {'success': True, 'env_config_template': result}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

