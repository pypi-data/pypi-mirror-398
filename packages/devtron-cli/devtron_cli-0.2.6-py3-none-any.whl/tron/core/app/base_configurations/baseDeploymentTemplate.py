import requests,json,os,copy,yaml
from tron.utils import DevtronUtils
from .baseConfigurationApproval import BaseConfigurationApproval
from jsonmerge import merge,Merger

class DeploymentTemplateHandler:
    def __init__(self, base_url, headers):
        self.base_url                    = base_url
        self.headers                     = headers
        self.devtron_utils               = DevtronUtils(base_url, headers)
        self.base_configuration_approval = BaseConfigurationApproval(base_url, headers)

    def setup_base_deployment_template(self, app_id, config_data):
        bdt = config_data.get('base_configurations').get('deployment_template', {})
        version      = bdt.get('version')
        chart_type   = bdt.get('chart_type')
        values_path  = bdt.get('values_path')  # optional: path to custom values.yaml
        values_patch = bdt.get('values_patch')  # optional: dict to patch globalConfig

        if not version or not chart_type:
            return {'success': False, 'error': 'deployment_template.version and chart_type are required in config'}
        
        # 1. Get chartRef id
        chartref_result = self.get_basedeployment_template_chart_id(app_id, version, chart_type)
        if not chartref_result['success']:
            return {'success': False, 'error': f"Failed to get chartRef id: {chartref_result['error']}"}
        chart_ref_id = chartref_result['id']
        print(f"Got chartRefId: {chart_ref_id} for appId: {app_id}, version: {version}, chart_type: {chart_type}")
        print(f"Fetching default values for appId: {app_id}, chartRefId: {chart_ref_id}")

        # 2. Get deployment template YAML
        yaml_result = self.get_deployment_template_yaml(app_id, chart_ref_id)
        if not yaml_result['success']:
            return {'success': False, 'error': f"Failed to get deployment template YAML: {yaml_result['error']}"}
        # Always use the structure under globalConfig.defaultAppOverride for defaultAppOverride
        global_config = yaml_result['yaml'].get('globalConfig', {}).get('defaultAppOverride', {})
        default_app_override = self._remove_newlines_from_strings(copy.deepcopy(global_config))
        values_override = None
        values_patch=None
        if values_path:
            # Load custom values file as JSON/dict (no YAML conversion needed for API)
            if not os.path.isfile(values_path):
                return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
            with open(values_path, 'r') as f:
                values_override = yaml.safe_load(f)
            values_override = self._remove_newlines_from_strings(values_override)
        else:
            values_patch=config_data.get('base_configurations', {}).get('deployment_template', {}).get('values_patch')
            values_patch_json = json.loads(json.dumps(values_patch)) 
            values_override = self._remove_newlines_from_strings(values_override)
            values_override = merge(global_config, values_patch_json)

        # 4. Save base deployment template
        show_application_metrics=config_data.get('base_configurations', {}).get('deployment_template', {}).get('show_application_metrics',"false")

        save_result = self.save_base_deployment_template(
            app_id, chart_ref_id, default_app_override, values_override=values_override if values_override is not None else None, id=0, show_application_metrics=show_application_metrics
        )
        if not save_result['success']:
            return {'success': False, 'error': f"Failed to save base deployment template: {save_result['error']}"}

        # After saving base deployment template, create config maps if present in config_data
        return {'success': True}
    def save_base_deployment_template(self, app_id, chart_ref_id, default_app_override, values_override=None, is_express_edit=False, resource_name="BaseDeploymentTemplate", id=None, config_approval={}, config_approval_in_base_deployment_template=None, show_application_metrics=False):
        """
        Save the base deployment template for a given app_id and chart_ref_id in Devtron.
        Args:
            app_id (int or str): The application ID
            chart_ref_id (int or str): The chartRef ID
            default_app_override (dict): The defaultAppOverride YAML as dict
            values_override (dict, optional): The valuesOverride YAML as dict (optional)
            is_express_edit (bool, optional): Whether this is an express edit (default: False)
            resource_name (str, optional): Resource name (default: "BaseDeploymentTemplate")
        Returns:
            dict: {success: bool, result: dict, error: str}
        """
        try:
            # Determine the operation type based on the presence of an ID. If a base deployment template for the same chart version already exists in the DB, update it using the existing ID. Otherwise, create a new record with a new ID.
            if not id:  # Covers None or 0
                operation = "create"
                url = f"{self.base_url}/orchestrator/app/template"
            else:
                operation = "update"
                url = f"{self.base_url}/orchestrator/app/template/update"
            # Build payload to match the working curl example exactly (field order and presence)
            payload = {
                "appId": int(app_id),
                "chartRefId": int(chart_ref_id),
                "defaultAppOverride": default_app_override,
                "saveEligibleChanges": False
            }
            if operation == "update" :
                payload["id"] = id
            # Always include valuesOverride, even if None
            payload["valuesOverride"] = values_override if values_override is not None else default_app_override
            payload["isExpressEdit"] = is_express_edit
            payload["resourceName"] = resource_name
            payload["isAppMetricsEnabled"]= show_application_metrics

            # Remove any None values recursively from the payload
            def remove_none(obj):
                if isinstance(obj, dict):
                    return {k: remove_none(v) for k, v in obj.items() if v is not None}
                elif isinstance(obj, list):
                    return [remove_none(i) for i in obj]
                else:
                    return obj
            payload = remove_none(payload)

            # Check for empty or None required fields
            if not isinstance(default_app_override, dict) or not default_app_override:
                print("defaultAppOverride is empty or not a dict!")
            if values_override is not None and (not isinstance(values_override, dict) or not values_override):
                print("valuesOverride is present but empty or not a dict!")

            # Use application/json content type instead of text/plain
            headers = dict(self.headers)
            headers['Content-Type'] = 'application/json'

            # Dump JSON 
            json_payload = json.dumps(payload, separators=(',', ':'), default=str)

            # print(url)
            # print(json_payload)
            # Send as UTF-8 encoded bytes
            if config_approval_in_base_deployment_template:
                base_deployment_template_create_draft_result = self.base_configuration_approval.base_deployment_template_create_draft(app_id=app_id, env_id=-1, data=json_payload, resource=3, resource_name=resource_name, action=2, config_approval=config_approval)
                if not base_deployment_template_create_draft_result.get('success'):
                    print("Failed to create draft:", base_deployment_template_create_draft_result.get('error'))
                    return {'success': False, 'error': 'Failed to create draft'}
                else:
                    return {'success': True, "message": 'Draft created successfully'}

            response = requests.post(url, headers=headers, data=json_payload.encode('utf-8'))
            
            # Try to parse response as JSON
            try:
                response_json = response.json()
                if response.status_code == 200:
                    result = response_json.get('result', {})

                    return {'success': True, 'result': result}
                else:
                    error_msg = response_json.get('errors', [{}])[0].get('userMessage', response.text)
                    return {'success': False, 'error': f'API request failed: {error_msg}'}
            except json.JSONDecodeError:
                # If response is not valid JSON, return the raw text
                if response.status_code == 200:
                    return {'success': True, 'result': {}, 'raw_response': response.text}
                else:
                    return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}
    def get_deployment_template_yaml(self, app_id, chart_ref_id):
        """
        Fetch the deployment template YAML for a given app_id and chart_ref_id from Devtron.
        Args:
            app_id (int or str): The application ID
            chart_ref_id (int or str): The chartRef ID
        Returns:
            dict: {success: bool, yaml: dict, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/app/template/{app_id}/{chart_ref_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json().get('result', {})
                return {'success': True, 'yaml': result}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}


    def get_basedeployment_template_chart_id(self, app_id, version, chart_type):
        """
        Fetch the chartRef id for a given app_id, version, and chart_type from Devtron.
        Args:
            app_id (int or str): The application ID (or string, as in the API)
            version (str): The chart version (e.g., '4.21.0')
            chart_type (str): The chart type/name (e.g., 'Deployment', 'Rollout Deployment', etc.)
        Returns:
            dict: {success: bool, id: int, error: str}
        """
        try:
            url = f"{self.base_url}/orchestrator/chartref/autocomplete/{app_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json().get('result', {})
                chart_refs = result.get('chartRefs', [])
                for ref in chart_refs:
                    if str(ref.get('version')) == str(version) and str(ref.get('name')) == str(chart_type):
                        return {'success': True, 'id': ref.get('id')}
                return {'success': False, 'error': f'No chartRef found for version={version}, chart_type={chart_type}'}
            else:
                return {'success': False, 'error': f'API request failed: {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}


    def _remove_newlines_from_strings(self, obj):
            """
            Recursively remove all \n from string values in a dict/list structure.
            """
            if isinstance(obj, dict):
                return {k: self._remove_newlines_from_strings(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [self._remove_newlines_from_strings(i) for i in obj]
            elif isinstance(obj, str):
                return obj.replace('\n', '')
            else:
                return obj


    def update_base_deployment_template(self, config_data,config_approval_in_base_deployment_template=None):
        app_id = self.devtron_utils.get_application_id_by_name(config_data.get('app_name')).get('app_id')
        chart_ref_id = self.get_latest_chart_ref_id(app_id)
        if not chart_ref_id:
            return {'success': False, 'error': 'Failed to get latest chart reference ID.'}
        # Proceed with updating the base deployment template using the chart_ref_id
        existing_bdt_result = self.get_deployment_template_yaml(app_id, chart_ref_id)
        if not existing_bdt_result['success']:
            return {'success': False, 'error': f"Failed to get existing deployment template: {existing_bdt_result['error']}"}

        existing_bdt = existing_bdt_result['yaml'].get('globalConfig')
        id=existing_bdt.get('id')
        check_if_diff_in_base_deployment_template_version_result = self.check_if_diff_in_base_deployment_template_version(existing_bdt, config_data)
        if check_if_diff_in_base_deployment_template_version_result['success']:
            print("There is a difference in base deployment template version.")
            chartref_result = self.get_basedeployment_template_chart_id(app_id, config_data.get('base_configurations', {}).get('deployment_template', {}).get('version'), config_data.get('base_configurations', {}).get('deployment_template', {}).get('chart_type'))
            if not chartref_result['success']:
                return {'success': False, 'error': f"Failed to get chartRef id: {chartref_result['error']}"}
            chart_ref_id = chartref_result['id']
            id=self.get_data_base_chart_ref_id(app_id, chart_ref_id)

        values_path = config_data.get('base_configurations', {}).get('deployment_template', {}).get('values_path')
        values_patch = config_data.get('base_configurations', {}).get('deployment_template', {}).get('values_patch')
        values_override = None
        
        if values_path:
            # Load custom values file as JSON/dict (no YAML conversion needed for API)
            if not os.path.isfile(values_path):
                return {'success': False, 'error': f"Custom values.yaml file not found: {values_path}"}
            with open(values_path, 'r') as f:
                values_override = yaml.safe_load(f)
            values_override = self._remove_newlines_from_strings(values_override)
        else:
            values_patch_json = json.loads(json.dumps(values_patch))
            values_override = merge(existing_bdt.get('defaultAppOverride'), values_patch_json)
        show_application_metrics = config_data.get('base_configurations', {}).get('deployment_template', {}).get('show_application_metrics')
        _diff = self.devtron_utils.compare_dicts(existing_bdt.get('defaultAppOverride'), values_override)
        if not _diff["success"]:
            return {"success": False, "error": f"Failed to check the diff between the deployment templates: {_diff['error']}"}
        if_diff = _diff.get("is_differ", True)
        if if_diff:

            save_base_deployment_template_result = self.save_base_deployment_template(app_id, chart_ref_id, existing_bdt.get('defaultAppOverride'), values_override=values_override, is_express_edit=False, resource_name="BaseDeploymentTemplate", id=id,config_approval=config_data.get('config_approval', {}),config_approval_in_base_deployment_template=config_approval_in_base_deployment_template, show_application_metrics=show_application_metrics)
            if not save_base_deployment_template_result['success']:
                return {'success': False, 'error': f"Failed to save base deployment template: {save_base_deployment_template_result['error']}"}
            else:
                return {'success': True, 'message': 'Base deployment template updated successfully.'}
        else:

            if check_if_diff_in_base_deployment_template_version_result['success']:
                save_base_deployment_template_result = self.save_base_deployment_template(app_id, chart_ref_id,
                                                                                          existing_bdt.get('defaultAppOverride'),
                                                                                          values_override=values_override,
                                                                                          is_express_edit=False,
                                                                                          resource_name="BaseDeploymentTemplate",
                                                                                          id=id,
                                                                                          config_approval=config_data.get(
                                                                                              'config_approval',
                                                                                              {}),
                                                                                          config_approval_in_base_deployment_template=config_approval_in_base_deployment_template,
                                                                                          show_application_metrics=show_application_metrics)
                if not save_base_deployment_template_result['success']:
                    return {'success': False,
                            'error': f"Failed to save base deployment template: {save_base_deployment_template_result['error']}"}
                else:
                    return {'success': True, 'message': 'Base deployment template updated successfully.'}


            if config_approval_in_base_deployment_template:
                draft = self.base_configuration_approval.get_base_deployment_template_drafts(app_id)
                if draft["success"]:
                    if draft.get("data", {}).get("draftId", 0):
                        draft_id = draft.get("data", {}).get("draftId", 0)
                        draft_version_id = draft.get("data", {}).get("draftVersionId", 0)
                        draft_state = draft.get("data", {}).get("draftState", 0)
                        if draft_state != 2:
                            delete_draft = self.base_configuration_approval.delete_draft_base_deployment_template(draft_id, draft_version_id, 2)
                            if not delete_draft["success"]:
                                return {'success': False, 'error': f"Failed to delete draft: {delete_draft['error']}"}
                            print("No diff in deployment template hence discarding the draft...")
                else:
                    return {'success': False, 'error': f"Failed to get draft: {draft['error']}"}


            return {'success': True, 'message': 'Base deployment template is up to date.'}


    def get_data_base_chart_ref_id(self, app_id, chart_ref_id):
        get_deployment_template_yaml_result = self.get_deployment_template_yaml(app_id, chart_ref_id)
        if get_deployment_template_yaml_result['success']:
            return get_deployment_template_yaml_result['yaml'].get('globalConfig', {}).get('id')
        else:
            print(f"Failed to get deployment template get data base chart ref id")
            return None


    def get_latest_chart_ref_id(self, app_id):
        latestAppChartRefResult = requests.get(f"{self.base_url}/orchestrator/chartref/autocomplete/{app_id}", headers=self.headers)
        if latestAppChartRefResult.status_code == 200:
            chart_ref_id = latestAppChartRefResult.json().get('result', {}).get('latestAppChartRef')
            return chart_ref_id
        return None


    def check_if_diff_in_base_deployment_template_version(self,existing_bdt,config_data):
        if existing_bdt.get('refChartTemplateVersion') != config_data.get('base_configurations', {}).get('deployment_template', {}).get('version') :
            return {'success': True, 'message': 'Base deployment template version is different.'}
        return {'success': False, 'message': 'Base deployment template version is the same.'}
