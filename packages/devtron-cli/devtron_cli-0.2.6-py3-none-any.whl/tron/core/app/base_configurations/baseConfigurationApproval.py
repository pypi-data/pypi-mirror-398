import requests,json

class BaseConfigurationApproval:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def base_deployment_template_create_draft(self, app_id, env_id, data, resource=3, resource_name="BaseDeploymentTemplate", action=2, config_approval={}):

        url = f"{self.base_url}/orchestrator/draft"
        changeProposed = None
        if config_approval.get('action') == "proposed":
            changeProposed = True
        else:
            changeProposed = False

        get_base_deployment_template_drafts_result = self.get_base_deployment_template_drafts(app_id)
        if get_base_deployment_template_drafts_result.get('success') and get_base_deployment_template_drafts_result.get('data').get('draftState') == 4:
                if config_approval.get('if_draft_already_exists') == "replace":
                    print("Existing draft found, proceeding to delete it.")
                    delete_draft_base_deployment_template_result = self.delete_draft_base_deployment_template(draftId=get_base_deployment_template_drafts_result.get('data').get('draftId'), draftVersionId=get_base_deployment_template_drafts_result.get('data').get('draftVersionId'), state=2)
                    if not delete_draft_base_deployment_template_result.get('success'):
                        return {'success': False, 'error': 'Failed to delete existing draft'}
                    else:
                        print("Existing draft deleted successfully.")
                elif config_approval.get('if_draft_already_exists') == "merge":
                    print("Existing draft found. Merging with existing draft.")
                    update_existing_draft_result = self.update_existing_draft(draftId=get_base_deployment_template_drafts_result.get('data').get('draftId'), lastDraftVersionId=get_base_deployment_template_drafts_result.get('data').get('draftVersionId'), action=action, data=data, userComment=config_approval.get('comments'), changeProposed=changeProposed)
                    if not update_existing_draft_result.get('success'):
                        return {'success': False, 'error': 'Failed to update existing draft'}
                    else:
                        return {'success': True, 'message': 'Draft updated successfully.'}
        else:
            print("No existing draft found, creating a new one.")
        
        payload = {
            "appId": int(app_id),
            "envId": int(env_id),
            "resource": int(resource),
            "resourceName": resource_name,
            "action": int(action),
            "data": data,
            "userComment": config_approval.get('comments', 'Draft created via CLI'),
            "changeProposed": changeProposed,
            "protectNotificationConfig": {"emailIds": []}
        }

        json_payload = json.dumps(payload)
        response = requests.post(url, headers=self.headers, data=json_payload.encode('utf-8'))

        if response.status_code == 200:
            return {'success': True, 'message': 'Draft created successfully.', 'data': response.json()}
        else:
            return {'success': False, 'error': f"Failed to create draft: {response.text}"}

    def delete_draft_base_deployment_template(self, draftId, draftVersionId, state):
        url = f"{self.base_url}/orchestrator/draft?draftId={draftId}&draftVersionId={draftVersionId}&state={state}"

        response = requests.put(url, headers=self.headers)

        if response.status_code == 200:
            return {'success': True, 'message': 'Draft deleted successfully.'}
        else:
            return {'success': False, 'error': f"Failed to delete draft: {response.text}"}

    def get_base_deployment_template_drafts(self, app_id):
        url = f"{self.base_url}/orchestrator/draft?resourceName=BaseDeploymentTemplate&resourceType=3&appId={app_id}&envId=-1"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            result=response.json().get('result')
            draftId=result.get("draftId")
            draftVersionId=result.get("draftVersionId")
            draftState=result.get("draftState")
            result={
                "draftId": draftId,
                "draftVersionId": draftVersionId,
                "draftState": draftState
            }
            return {'success': True, 'message': 'Drafts retrieved successfully.', 'data': result}
        else:
            return {'success': False, 'error': f"Failed to retrieve drafts: {response.text}"}
        
    def update_existing_draft(self, draftId, lastDraftVersionId, action=2, data=None,
        userComment="", changeProposed=False, protectNotificationConfig=None):

        url = f"{self.base_url}/orchestrator/draft/version"

        # Ensure `data` is a JSON string in the payload (API expects stringified JSON)
        if data is None:
            data_str = ""
        elif isinstance(data, str):
            data_str = data
        else:
            # compact serialization to keep payload small
            data_str = json.dumps(data, separators=(",", ":"))

        payload = {
            "draftId": int(draftId),
            "lastDraftVersionId": int(lastDraftVersionId),
            "action": int(action),
            "data": data_str,
            "userComment": userComment ,
            "changeProposed": bool(changeProposed) ,
            "protectNotificationConfig": protectNotificationConfig or {"emailIds": []}
        }

        # Use a copy of headers and ensure correct Content-Type
        headers = dict(self.headers) if hasattr(self, 'headers') and self.headers else {}
        headers.setdefault('Content-Type', 'application/json')

        response = requests.put(url, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                resp_json = response.json()
            except Exception:
                resp_json = {"text": response.text}
            return {'success': True, 'message': 'Draft updated successfully.'}
        else:
            return {'success': False, 'error': f"Failed to update draft: {response.text}", 'status_code': response.status_code}
