import requests, json
from tron.utils import DevtronUtils
class DevtronAppMetadata:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.utils = DevtronUtils(base_url, headers)
    def save_metadata(self, config_data):
        try:
            app_name = config_data.get('app_name')
            project_name = config_data.get('project_name')
            description = config_data.get('description', '')
            labels = config_data.get('labels', [])
            if not app_name or not project_name:
                return {
                    'success': False,
                    'error': 'app_name and project_name are required'
                }
            # Get IDs
            project_result = self.utils.get_team_id_by_project_name(project_name)
            if not project_result.get('success'):
                return {'success': False, 'error': f"Could not get team ID: {project_result.get('error', '')}"}
            project_id = project_result['team_id']
            app_result = self.utils.get_application_id_by_name(app_name)
            if not app_result.get('success'):
                return {'success': False, 'error': f"Could not get app ID: {app_result.get('error', '')}"}
            app_id = app_result['app_id']

            # Prepare payload
            payload = {
                'id': app_id,
                'teamId': project_id,
                'description': description,
                'labels': labels

            }

            url = f"{self.base_url}/orchestrator/app/edit"
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200:
                return {'success': True, 'result': response.json()}
            else:
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', response.text)
                    return {'success': False, 'error': f'API request failed: {error_message}'}
                except Exception:
                    return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}
