import requests, json, yaml, os

class DevtronOverrideConfigMapSecret:
    def __init__(self, base_url, headers):
        self.base_url        = base_url
        self.headers         = headers



    def get_override_cm_cs_list(self, app_id,env_id):
        # getting list of cm cs from the applications for environment
        try:
            url = f"{self.base_url}/orchestrator/config/autocomplete?appId={app_id}&envId={env_id}"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            response_json = response.json()
            cm_list = []
            cs_list = []
            resourceConfigId=None
            if response.status_code == 200:
                result = response_json.get('result', {})
                for item in result.get('resourceConfig'):
                    # get the configuration type
                    cm_cs_type = item.get('type')
                    # get the config stage type whether it is overridden or created at env level
                    configStage = item.get('configStage')
                    if cm_cs_type == 'ConfigMap' and (configStage == 'Env' or configStage == 'Overridden'):
                        cm_list.append(item.get('name'))
                    elif cm_cs_type == 'Secret' and (configStage == 'Env' or configStage == 'Overridden'):
                        cs_list.append(item.get('name'))
                    elif cm_cs_type == 'Deployment Template':
                        continue
                    if resourceConfigId is None and (configStage == 'Env' or configStage == 'Overridden'):  # assign only once
                        resourceConfigId = item.get('id')

                return {'success': True, 'result': {'cm_list': cm_list, 'cs_list': cs_list, 'resourceConfigId': resourceConfigId}}
            
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_override_config_map_details(self, app_name, env_name, config_map_name, resource_id):
        """
        Get detailed information for a specific config map.
        
        Args:
            app_name (str): The application Name
            env_name (str): Environment Name
            config_map_name (str): Name of the config map
            resource_id (int): Id of the resource
            
        Returns:
            dict: Detailed config map information including data, type, mountPath, etc.
        """
        try:            
            # Get detailed config map data
            # orchestrator/config/data?appName={app_name}&envName={env_name}&configType=PublishedOnly&resourceId={resource_id}&resourceName=config_map_name&resourceType=ConfigMap
            url = f"{self.base_url}/orchestrator/config/data?appName={app_name}&envName={env_name}&configType=PublishedOnly&resourceId={resource_id}&resourceName={config_map_name}&resourceType=ConfigMap"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json().get('result', {})
                config_map_data = result.get('configMapData', {}).get('data',{}).get('configData',[])[0]
                
                return {
                    'success': True,
                    'config_map': config_map_data
                }
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

    def get_override_secret_details(self, app_name, env_name, secret_name, resource_id):
        """
        Get detailed information for a specific secret.
        
        Args:
            app_name (str): The application Name
            env_name (str): Environment Name
            resource_id (int): Id of the resource
            secret_name (str): Name of the secret
            
        Returns:
            dict: Detailed secret information including data, type, mountPath, etc.
        """
        try:
            # Get detailed secret data
            url = f"{self.base_url}/orchestrator/config/data?appName={app_name}&envName={env_name}&configType=PublishedOnly&resourceId={resource_id}&resourceName={secret_name}&resourceType=Secret"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json().get('result', {})
                secrets = result.get('secretsData', {}).get('data',{}).get('configData',[])[0]
                return {
                    'success': True,
                    'secret': secrets
                }
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}