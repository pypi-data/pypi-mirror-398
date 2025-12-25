import requests, json, yaml, os
from tron.utils import DevtronUtils
from tron.core.app.base_configurations.configMapSecretApproval import ConfigMapSecretApproval

class DevtronConfigMapSecret:
    def __init__(self, base_url, headers):
        self.base_url        = base_url
        self.headers         = headers
        self.devtron_utils   = DevtronUtils(base_url, headers)
        self.config_approval = ConfigMapSecretApproval(base_url, headers)

    def create_secret(self, app_id, secret_data, config_approval_in_base_secret=None, id=None):
        """
        Create a secret for the given app_id in Devtron.
        Args:
            app_id (int or str): The application ID
            secret_data (dict): Should be a dict with keys:
                - name (str): Secret name
                - type (str): Secret type (e.g., 'environment')
                - external (bool): Optional, default False
                - data (dict): Dict of key: base64-encoded value
                - roleARN (str or None): Optional
                - externalType (str or None): Optional
                - esoSecretData (any): Optional
                - mountPath (str or None): Optional
                - subPath (str or None): Optional
                - filePermission (str or None): Optional
                - esoSubPath (str or None): Optional
                - mergeStrategy (str or None): Optional
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/config/global/cs"
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
            
            payload = {
                "appId": int(app_id),
                "configData": [secret_data_full],
                "isExpressEdit": False
            }
            if id is not None:
                payload["id"] = id
            headers = dict(self.headers)
            headers['Content-Type'] = 'text/plain;charset=UTF-8'
            json_payload = json.dumps(payload, separators=(",", ":"), default=str)
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


    def delete_secret(self, app_id, secret_name, resourceConfigId):
        url = f"{self.base_url}/orchestrator/config/global/cs/{app_id}/{resourceConfigId}?name={secret_name}&isExpressEdit=false"
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        response = requests.delete(url, headers=headers)
        if response.status_code == 200:
            return {'success': True, 'message': 'Secret deleted successfully'}
        else:
            return {'success': False, 'error': f'API request failed: {response.text}'}


    def create_config_map(self, app_id, config_map_data, config_approval_in_base_config_map=False, id=None):
        """
        Create a config map (CM) for the given app_id in Devtron.
        Args:
            config_approval_in_base_config_map(bool): Whether config approval is enabled for base config maps
            id (int or None): Optional, resourceConfigId for updating existing config map
            app_id (int or str): The application ID
            config_map_data (dict): Should be a dict with keys:
                - name (str): ConfigMap name
                - type (str): ConfigMap type (e.g., 'environment')
                - external (bool): Optional, default False
                - data (dict): Dict of key: value
                - roleARN (str or None): Optional
                - externalType (str or None): Optional
                - esoSecretData (any): Optional
                - mountPath (str or None): Optional
                - subPath (str or None): Optional
                - filePermission (str or None): Optional
                - esoSubPath (str or None): Optional
                - mergeStrategy (str or None): Optional
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:

            url = f"{self.base_url}/orchestrator/config/global/cm"
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

            if not config_approval_in_base_config_map:
                payload = {
                    "appId": int(app_id),
                    "configData": [config_map_data_full],
                    "isExpressEdit": False
                }
                if id is not None:
                    payload["id"] = id
                headers = dict(self.headers)
                headers['Content-Type'] = 'text/plain;charset=UTF-8'
                json_payload = json.dumps(payload, separators=(",", ":"), default=str)
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
            else:
                print("Config approval is enabled for base config map. Creating draft instead of direct creation.")
                approval_config_update_result = self.config_approval.create_base_cm_cs_draft(app_id,env_id=-1,resource_type=1,resource_name=config_map_data.get('name'), action=1,cm_cs_data=config_map_data_full, user_comment="Creating/Updating base config map with config approval.")
                if not approval_config_update_result['success']:
                    return {'success': False, 'error': f"Failed to create/update draft: {approval_config_update_result['error']}"}
                return {'success': True, 'result': approval_config_update_result}

        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def delete_config_map(self, app_id, config_map_name,config_map_approval_enabled, resourceConfigId):
        url = f"{self.base_url}/orchestrator/config/global/cm/{app_id}/{resourceConfigId}?name={config_map_name}&isExpressEdit=false"
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        try:
            response = requests.delete(url, headers=headers)
            if response.status_code == 200:
                return {'success': True, 'message': 'Config map deleted successfully'}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'API request failed: {str(e)}'}


    def get_base_cm_cs_details(self, app_id):
        # getting cm cs from the applications then will decide whom to delete and to create new one
        try:
            # envId is set to -1 to fetch base config maps and secrets
            url = f"{self.base_url}/orchestrator/config/autocomplete?appId={app_id}&envId=-1"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            response_json = response.json()
            cm_list = []
            cs_list = []
            resourceConfigId=None  #used to delete or update cm/cs
            if response.status_code == 200:
                result = response_json.get('result', {})
                for item in result.get('resourceConfig'):
                    if item.get('type') == 'ConfigMap':
                        cm_list.append(item.get('name'))
                    elif item.get('type') == 'Secret':
                        cs_list.append(item.get('name'))
                    elif item.get('type') == 'Deployment Template':
                        continue
                    if resourceConfigId is None:  # assign only once
                        resourceConfigId = item.get('id')

                return {'success': True, 'result': {'cm_list': cm_list, 'cs_list': cs_list, 'resourceConfigId': resourceConfigId}}
            
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_config_map_details(self, app_id, config_map_name):
        """
        Get detailed information for a specific config map.
        
        Args:
            app_id (int): The application ID
            config_map_name (str): Name of the config map
            
        Returns:
            dict: Detailed config map information including data, type, mountPath, etc.
        """
        try:
            # First get the resource config ID for the config map
            cm_cs_details = self.get_base_cm_cs_details(app_id)
            if not cm_cs_details['success']:
                return cm_cs_details
            
            # Get detailed config map data
            url = f"{self.base_url}/orchestrator/config/global/cm/{app_id}"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json().get('result', {})
                config_maps = result.get('configData', [])
                
                # Find the config map with matching name
                for config_map in config_maps:
                    if config_map.get('name') == config_map_name:
                        return {
                            'success': True,
                            'config_map': config_map
                        }
                
                return {'success': False, 'error': f'Config map {config_map_name} not found'}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_secret_details(self, app_id, secret_name):
        """
        Get detailed information for a specific secret.
        
        Args:
            app_id (int): The application ID
            secret_name (str): Name of the secret
            
        Returns:
            dict: Detailed secret information including data, type, mountPath, etc.
        """
        try:
            # First get the resource config ID for the secret
            cm_cs_details = self.get_base_cm_cs_details(app_id)
            if not cm_cs_details['success']:
                return cm_cs_details
            
            # Get detailed secret data
            url = f"{self.base_url}/orchestrator/config/global/cs/{app_id}"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json().get('result', {})
                secrets = result.get('configData', [])
                
                # Find the secret with matching name
                for secret in secrets:
                    if secret.get('name') == secret_name:
                        return {
                            'success': True,
                            'secret': secret
                        }
                
                return {'success': False, 'error': f'Secret {secret_name} not found'}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def is_cm_cs_modified(self, app_id: int, new_config: dict, resource_type: str):
        """
        Compares the new_config with the current config in devtron to check for modifications.
        Args:
            app_id (int): The application ID.
            new_config (dict): The new configuration data for the ConfigMap or Secret.
            resource_type (str): The type of resource, either 'cm' for ConfigMap or 'cs' for Secret.

        Returns:
            dict: {'success': bool, 'modified': bool, 'error': str}
        """
        try:
            if not new_config or 'name' not in new_config:
                return {"success": False, "modified": False, "error": "The config was not provided or is missing a name."}

            config_name = new_config['name']

            if resource_type == 'cm':
                details_result = self.get_config_map_details(app_id, config_name)
                current_config = details_result.get('config_map')
            elif resource_type == 'cs':
                details_result = self.get_secret_details(app_id, config_name)
                current_config = details_result.get('secret')
            else:
                return {"success": False, "modified": False, "error": f"Invalid resource_type: {resource_type}"}

            if not details_result['success'] or not current_config:
                # If it doesn't exist, it's not a modification but a creation, but for safety we can say not modified.
                return {"success": False, "modified": False, "error": f"Could not fetch current details for {config_name}."}

            # Fields to compare
            fields_to_check = [
                'type', 'external', 'data', 'mountPath', 'subPath',
                'filePermission', 'externalType', 'roleARN', 'mergeStrategy'
            ]


            default_values = {
                'name': "",
                'type': "volume",
                'external': False,
                'data': {},
                'mountPath': "",
                'subPath': "",
                'filePermission': "",
                'externalType': "",
                'roleARN': "",
                'mergeStrategy': "",
                'patchData': None,
                'global': True,
                'esoSecretData': None,
                'defaultESOSecretData': None,
                'esoSubPath': None
            }
            if new_config.get("subPath", ""):
                default_values["type"] = "volume"
            else:
                default_values["type"] = "environment"

            for field in fields_to_check:

                new_value = new_config.get(field, default_values.get(field))
                current_value = current_config.get(field, default_values.get(field))

                # Normalize 'data' field for comparison if it's None or empty
                if field == 'data':
                    new_value = new_value or {}
                    current_value = current_value or {}

                if new_value != current_value:
                    return {"success": True, "modified": True}

            return {"success": True, "modified": False}

        except Exception as e:
            return {'success': False, 'modified': False, 'error': f'Exception occurred: {str(e)}'}




    def update_base_cm_cs(self, config_data: dict = None, config_approval_in_base_config_map=None,config_approval_in_base_secret=None, allow_deletion=False):
        app_id = self.devtron_utils.get_application_id_by_name(config_data.get('app_name')).get('app_id')
        get_base_cm_cs_details_result = self.get_base_cm_cs_details(app_id)
        if not get_base_cm_cs_details_result['success']:
            return {
                'success': False,
                'error': f"Failed to fetch existing config maps and secrets: {get_base_cm_cs_details_result['error']}"
            }
        existing_cm_cs        = get_base_cm_cs_details_result.get('result', {})
        existing_cm_names     = existing_cm_cs.get('cm_list', [])
        resource_config_id    = existing_cm_cs.get('resourceConfigId', None)
        existing_secret_names = existing_cm_cs.get('cs_list', [])


        current_cm_names = [item.get('name') for item in config_data.get('base_configurations', {}).get('config_maps', [])]
        current_cs_names = [item.get('name') for item in config_data.get('base_configurations', {}).get('secrets', [])]

        cm_to_create = []
        cm_to_update = []
        cm_to_delete = []

        cs_to_create = []
        cs_to_update = []
        cs_to_delete = []

        # Start by assuming all existing config maps need to be deleted
        cm_to_delete = existing_cm_names
        for item in current_cm_names:
            if item in existing_cm_names:
                # Item exists in both current and existing → mark it for update
                cm_to_update.append(item)

                # Remove from delete list since it exists in both
                cm_to_delete.remove(item)
            else:
                # Item exists in current but not in existing → mark it for creation
                cm_to_create.append(item)

        # Start by assuming all existing secrets need to be deleted
        cs_to_delete = existing_secret_names
        for item in current_cs_names:
            if item in existing_secret_names:
                # Item exists in both current and existing → mark it for update
                cs_to_update.append(item)

                # Remove from delete list since it exists in both
                cs_to_delete.remove(item)
            else:
                # Item exists in current but not in existing → mark it for creation
                cs_to_create.append(item)

        # Check if there are any deletions and if allow_deletion is False
        if (cm_to_delete or cs_to_delete) and not allow_deletion:
            deletion_list = []
            if cm_to_delete:
                deletion_list.extend([f"ConfigMap: {name}" for name in cm_to_delete])
            if cs_to_delete:
                deletion_list.extend([f"Secret: {name}" for name in cs_to_delete])
            
            deletion_message = "The following resources will be deleted:\n" + "\n".join(deletion_list)
            deletion_message += "\n\nTo proceed with deletion, please add the --allow-deletion flag to the update-app command."
            
            return {
                'success': False,
                'error': f'Deletion requires explicit approval. {deletion_message}'
            }

        cm_data = config_data.get('base_configurations', {}).get('config_maps')
        cm_to_create_data=[]
        cm_to_update_data=[]
        cm_list = cm_data if isinstance(cm_data, list) else [cm_data]
        for cm in cm_list:
            if 'from_file' in cm:
                values_path = cm.get('from_file')
                if not os.path.isfile(values_path):
                    return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                with open(values_path, 'r') as f:
                    cm_file_data = yaml.safe_load(f)
                    cm['data'] = cm_file_data

            if cm.get('name') in cm_to_create:
                cm_to_create_data.append(cm)
            if cm.get('name') in cm_to_update:
                if_cm_has_changes = self.is_cm_cs_modified(app_id, cm, "cm")
                if if_cm_has_changes.get("modified", True):
                    cm_to_update_data.append(cm)
        for item in cm_to_create_data:
            cm_result = self.create_config_map(app_id, item, config_approval_in_base_config_map)
            if not cm_result['success']:
                return {'success': False, 'error': f"Failed to create config map: {cm_result['error']}"}

        for item in cm_to_update_data:
            cm_result = self.create_config_map(app_id, item,config_approval_in_base_config_map,id=resource_config_id)
            if not cm_result['success']:
                return {'success': False, 'error': f"Failed to update config map: {cm_result['error']}"}
        
        for item in cm_to_delete:
            cm_result = self.delete_config_map( app_id, item,config_approval_in_base_config_map, resource_config_id)
            if not cm_result['success']:
                return {'success': False, 'error': f"Failed to delete config map: {cm_result['error']}"}

        cs_data = config_data.get('base_configurations', {}).get('secrets')
        cs_to_create_data=[]
        cs_to_update_data=[] 
        cs_list = cs_data if isinstance(cs_data, list) else [cs_data]   
        for cs in cs_list:
            if 'from_file' in cs:
                values_path = cs.get('from_file')
                if not os.path.isfile(values_path):
                    return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                with open(values_path, 'r') as f:
                    cs_file_data = yaml.safe_load(f)
                    cs['data'] = cs_file_data
            if cs.get('name') in cs_to_create:
                cs_to_create_data.append(cs)
            if cs.get('name') in cs_to_update:
                cs_to_update_data.append(cs)
        for item in cs_to_create_data:
            secret_b64 = self.devtron_utils.makebase64(item)
            cs_result = self.create_secret(app_id, secret_b64, config_approval_in_base_secret)
            if not cs_result['success']:
                return {'success': False, 'error': f"Failed to create secret: {cs_result['error']}"}
        for item in cs_to_update_data:
            secret_b64 = self.devtron_utils.makebase64(item)
            cs_result = self.create_secret(app_id, secret_b64, config_approval_in_base_secret, id=resource_config_id)
            if not cs_result['success']:
                return {'success': False, 'error': f"Failed to update secret: {cs_result['error']}"}
        for item in cs_to_delete:
            cs_result = self.delete_secret( app_id, item, config_approval_in_base_secret)
            if not cs_result['success']:
                return {'success': False, 'error': f"Failed to delete secret: {cs_result['error']}"}     
        return {'success': True, 'message': 'Base config map and secret operations completed successfully.'}
