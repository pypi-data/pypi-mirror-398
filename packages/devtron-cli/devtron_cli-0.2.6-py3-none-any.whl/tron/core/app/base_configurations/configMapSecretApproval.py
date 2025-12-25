import requests
import json


class ConfigMapSecretApproval:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def create_base_cm_cs_draft(self, app_id, env_id, resource_type, resource_name, action, cm_cs_data, user_comment=""):
        """
        Create a draft for ConfigMap/Secret changes that require approval.
        
        Args:
            app_id (int): Application ID
            env_id (int): Environment ID (-1 for base config)
            resource_type (int): 1 for ConfigMap, 2 for Secret
            resource_name (str): Name of the resource
            action (int): Action type (2 for create/update, 3 for delete)
            cm_cs_data (dict): JSON string of config data
            user_comment (str): Optional user comment
        
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:

            url = f"{self.base_url}/orchestrator/draft"
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

            
            headers = dict(self.headers)
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
    def get_base_cm_cs_draft(self, app_id, env_id, resource_type, resource_name):
        """
        Get draft details for ConfigMap/Secret changes.
        
        Args:
            app_id (int): Application ID
            env_id (int): Environment ID (-1 for base config)
            resource_type (int): 1 for ConfigMap, 2 for Secret
            resource_name (str): Name of the resource
        
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/draft"
            
            params = {
                'resourceName': resource_name,
                'resourceType': resource_type,
                'appId': app_id,
                'envId': env_id
            }
            
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'

            response = requests.get(url, headers=headers, params=params)
            
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

    def update_base_cm_cs_draft(self, draft_id, last_draft_version_id, action, cm_cs_data, user_comment=""):
        """
        Update an existing draft for ConfigMap/Secret changes.
        
        Args:
            draft_id (int): Draft ID
            last_draft_version_id (int): Last draft version ID
            action (int): Action type (2 for create/update, 3 for delete)
            cm_cs_data (str): JSON string of config data
            user_comment (str): Optional user comment
        
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/draft/version"
            
            payload = {
                "draftId": int(draft_id),
                "lastDraftVersionId": int(last_draft_version_id),
                "action": int(action),
                "data": cm_cs_data,
                "userComment": user_comment,
                "changeProposed": True
            }
            
            headers = dict(self.headers)
            headers['Content-Type'] = 'text/plain;charset=UTF-8'
            
            json_payload = json.dumps(payload, separators=(",", ":"), default=str)
            response = requests.put(url, headers=headers, data=json_payload.encode('utf-8'))
            
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

    def delete_base_cm_cs_draft(self, draft_id, last_draft_version_id, resource_config_id, user_comment=""):
        """
        Delete a draft for ConfigMap/Secret changes.
        
        Args:
            draft_id (int): Draft ID
            last_draft_version_id (int): Last draft version ID
            resource_config_id (int): Resource config ID
            user_comment (str): Optional user comment
        
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/draft/version"
            
            payload = {
                "draftId": int(draft_id),
                "lastDraftVersionId": int(last_draft_version_id),
                "action": 3,  # 3 for delete action
                "data": json.dumps({"id": int(resource_config_id)}),
                "userComment": user_comment,
                "changeProposed": True
            }
            
            headers = dict(self.headers)
            headers['Content-Type'] = 'text/plain;charset=UTF-8'
            
            json_payload = json.dumps(payload, separators=(",", ":"), default=str)
            response = requests.put(url, headers=headers, data=json_payload.encode('utf-8'))
            
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
