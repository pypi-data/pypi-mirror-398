import os,yaml,requests
from tron.utils import DevtronUtils
from .baseDeploymentTemplate import DeploymentTemplateHandler
from .configMapSecret import DevtronConfigMapSecret

class BaseConfiguration:
    def __init__(self, base_url, headers):
        self.base_url                  = base_url
        self.headers                   = headers
        self.bdt                       = DeploymentTemplateHandler(base_url, headers)
        self.devtron_config_map_secret = DevtronConfigMapSecret(base_url, headers)
        self.devtron_utils             = DevtronUtils(base_url, headers)
        
    def setup_base_configurations(self, app_id, config_data):

        print("Setting up base deployment template...")
        base_deploy_result = self.bdt.setup_base_deployment_template(app_id, config_data)
        if not base_deploy_result['success']:
            return {
                'success': False,
                'error': f"Application created but failed to setup base deployment template: {base_deploy_result['error']}"
            }

        cm_data = config_data.get('base_configurations', {}).get('config_maps')
        if cm_data:
            cm_list = cm_data if isinstance(cm_data, list) else [cm_data]
            for cm in cm_list:
                if 'from_file' in cm:
                    values_path = cm.get('from_file')
                    if not os.path.isfile(values_path):
                        return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                    with open(values_path, 'r') as f:
                        cm_file_data = yaml.safe_load(f)
                    cm['data'] = cm_file_data
                print(f"Creating config map for appId: {app_id} with provided data: {cm.get('name')}")
                cm_result = self.devtron_config_map_secret.create_config_map(app_id, cm)
                if not cm_result['success']:
                    return {'success': False, 'error': f"Base deployment template saved, but failed to create config map: {cm_result['error']}"}
            print("All config maps created successfully!")

        # After config maps, create secrets if present in config_data
        secret_data = config_data.get('base_configurations', {}).get('secrets')
        if secret_data:
            secret_list = secret_data if isinstance(secret_data, list) else [secret_data]
            for secret in secret_list:
                if 'from_file' in secret:
                    values_path = secret.get('from_file')
                    if not os.path.isfile(values_path):
                        return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
                    with open(values_path, 'r') as f:
                        secret_file_data = yaml.safe_load(f)
                    secret['data'] = secret_file_data
                secret_b64 = self.devtron_utils.makebase64(secret)
                print(f"Creating secret for appId: {app_id} with data: {secret.get('name')}")
                secret_result = self.devtron_config_map_secret.create_secret(app_id, secret_b64)
                if not secret_result['success']:
                    return {'success': False, 'error': f"Base deployment template and config map saved, but failed to create secret: {secret_result['error']}"}
            print("All secrets created successfully!")
        return {'success': True}


    def update_base_configurations(self, config_data, allow_deletion=False):
        app_id = self.devtron_utils.get_application_id_by_name(config_data.get('app_name')).get('app_id')
        check_if_config_approvals_exist_result = self.check_if_config_approvals_exist_in_base_configuration(app_id)
        if not check_if_config_approvals_exist_result['success']:
            return {
                'success': False,
                'error': f"Failed to check config approvals: {check_if_config_approvals_exist_result['error']}"
            }
        config_approval_in_base_deployment_template=None
        config_approval_in_base_config_map=None
        config_approval_in_base_secret=None
        if check_if_config_approvals_exist_result.get('data') != []:
            # Handle the case where config approvals exist
            for item in check_if_config_approvals_exist_result.get('data'):
                if item == "configuration/deployment-template":
                    print("Active config approvals found for base configurations deployment template.")
                    config_approval_in_base_deployment_template= True
                elif item == "configuration/config-map":
                    print("Active config approvals found for base configurations configmap.")
                    config_approval_in_base_config_map= True
                elif item == "configuration/config-secret":
                    print("Active config approvals found for base configurations secret.")
                    config_approval_in_base_secret= True

        else :
            print("No active config approvals found for base configurations.")
        print("Updating base deployment template...")
        base_deploy_result = self.bdt.update_base_deployment_template(config_data,config_approval_in_base_deployment_template)
        if not base_deploy_result['success']:
            return {
                'success': False,
                'error': f"Failed to update base deployment template: {base_deploy_result['error']}"
            }
        if config_approval_in_base_deployment_template:
            print("Base deployment template draft created/updated successfully!")
        else:
            print("Base deployment template updated without config approval.")

        update_base_cm_cs_result = self.devtron_config_map_secret.update_base_cm_cs(config_data,config_approval_in_base_config_map,config_approval_in_base_secret, allow_deletion)
        if not update_base_cm_cs_result['success']:
            return {
                'success': False,
                'error': f"Base deployment template updated, but failed to update config maps and secrets: {update_base_cm_cs_result['error']}"
            }
        print("Base config maps and secrets updated successfully!")

        return {'success': True , 'message': base_deploy_result.get('message', {})}


    def check_if_config_approvals_exist_in_base_configuration(self, app_id):
        get_config_approval_result= requests.get(f"{self.base_url}/orchestrator/protect/v2?appId={app_id}", headers=self.headers)
        approval_scope= []
        if get_config_approval_result.status_code == 200:
            for result in get_config_approval_result.json().get('result'):
                # state 1 mean config approval is active and envId -1 means its for base deployment template
                if result.get('envId') == -1  and result.get('state') == 1:
                    for approval in result.get('approvalConfigurations', []):
                        approval_scope.append(approval.get('kind'))
            return {'success': True, 'data': approval_scope}
        return {'success': False, 'error': f"Failed to get config approvals: {get_config_approval_result.text}"}
