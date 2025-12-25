import requests
import json
from .githandler import GitHandler
from tron.utils import DevtronUtils

class UpdateGitHandler:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.git_handler = GitHandler(base_url, headers)
        self.utils = DevtronUtils(base_url, headers)
    def update_git_materials(self, config_data):
        try:
            app_name = config_data.get('app_name')
            if not app_name:
                return {
                    'success': False,
                    'error': 'app_name is required in config_data'
                }
            # Get application ID
            app_name = config_data.get('app_name')
            app_result = self.utils.get_application_id_by_name(app_name)
            if not app_result.get('success'):
                return {'success': False, 'error': f"Could not get app ID: {app_result.get('error', '')}"}
            app_id = app_result['app_id']

            current_git_materials = self.git_handler.get_current_git_materials(app_id).get('materials', [])

            input_git_materials = config_data.get('git_repositories', [])

            # finding unique key for current and input git materials
            current_git_materials_map = []
            for item in current_git_materials:
                unique_key = self.makeGitPrimaryKey(item.get('url'), item.get('checkoutPath'))
                current_git_materials_map.append(unique_key)
            
            input_git_materials_map = []
            for item in input_git_materials:
                unique_key = self.makeGitPrimaryKey(item.get('url'), item.get('checkout_path'))
                input_git_materials_map.append(unique_key)

            has_diff, materials_to_remove, materials_to_add = self.is_git_materials_different(current_git_materials_map, input_git_materials_map)
            if has_diff:
                print("There is difference in git materials, updating git materials...")
                # adding condition to check if there are materials to add or update
                if len(materials_to_add) > 0:
                    current_checkout_paths = [item.get('checkoutPath') for item in current_git_materials]
                    for item in materials_to_add:
                        input_checkout_path = item.strip().split("::")[1]
                        if input_checkout_path in current_checkout_paths:
                            print(f"Updating existing git material which have checkout path-: {input_checkout_path}")
                            update_git_materials_by_id_result = self.update_existing_git_material_by_id(app_id, current_git_materials, item)
                            if not update_git_materials_by_id_result.get('success'):
                                return {
                                    'success': False,
                                    'error': f"Failed to update git materials: {update_git_materials_by_id_result.get('error', '')}"
                                }
                            materials_to_add.remove(item)
                            
                add_git_materials_result = self.add_git_materials(app_id, input_git_materials, materials_to_add)
                if not add_git_materials_result.get('success'):
                    return {
                        'success': False,
                        'error': f"Failed to add git materials: {add_git_materials_result.get('error', '')}"
                    }
                remove_git_materials_result = self.remove_git_materials(app_id, current_git_materials, materials_to_remove)
                if not remove_git_materials_result.get('success'):
                    return {
                        'success': False,
                        'error': f"Failed to remove git materials: {remove_git_materials_result.get('error', '')}"
                    }
                print("Git materials updated successfully.")
                return {'success': True, 'message': 'Git materials updated successfully.'}
            else:
                print("No difference in git materials, skipping git material update.")
                return {'success': True, 'message': 'No difference in git materials.'}

        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }
    def add_git_materials(self, app_id, input_git_materials, materials_to_add):
        url = f"{self.base_url}/orchestrator/app/material"
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        for material in input_git_materials:
            unique_key = self.makeGitPrimaryKey(material.get('url'), material.get('checkout_path'))
            if unique_key in materials_to_add:
                provider_result = self.git_handler.get_git_provider_id_by_name(material.get('git_account_name'))
                materials_payload = {
                    'url': material.get('url'),
                    'checkoutPath': material.get('checkout_path'),
                    'gitProviderId': provider_result.get('git_provider_id'),
                    'fetchSubmodules': material.get('fetch_submodules'),
                    'filterPattern': material.get('filter_pattern')
                }

                payload = {
                    'appId': app_id,
                    'material': [materials_payload]
                }
                
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Material added successfully."
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to add material: {response.text}"
                    }
        return {'success': True, 'message': 'No materials to add.'}
    def remove_git_materials(self, app_id, current_git_materials, materials_to_remove):
        url = f"{self.base_url}/orchestrator/app/material/delete"
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        for material in current_git_materials:
            unique_key = self.makeGitPrimaryKey(material.get('url'), material.get('checkoutPath'))
            if unique_key in materials_to_remove:
                payload = {
                    "appId": app_id,
                    "material": material
                }
                response = requests.delete(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "Material removed successfully."
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to remove material: {response.text}"
                    }
        return {'success': True, 'message': 'No materials to remove.'}
    def update_existing_git_material_by_id(self, app_id, current_git_materials, repourlwithpath):
        url = f"{self.base_url}/orchestrator/app/material"
        headers = dict(self.headers)
        headers['Content-Type'] = 'application/json'
        for item in current_git_materials:
            unique_key = item.get('checkoutPath')
            if unique_key == repourlwithpath.strip().split("::")[1]:
                item['url'] = repourlwithpath.split("::")[0]
                payload = {
                    "appId": app_id,
                    "material": item
                }
                response = requests.put(url, headers=headers, data=json.dumps(payload))
                if response.status_code == 200:
                    return {"success": True, "message": "Material updated successfully."}
                else:
                    return {"success": False, "error": f"Failed to update material: {response.text}"}
        return {"success": False, "error": "Material to update not found."}
    def makeGitPrimaryKey(self, git_material_url, checkout_path):
        return f"{git_material_url}::{checkout_path}"
    def is_git_materials_different(self,current_git_materials,input_git_materials): 
        materials_to_remove = []
        materials_to_add = input_git_materials
        for item in current_git_materials:
            if item in input_git_materials:
                materials_to_add.remove(item)
            else:  
                materials_to_remove.append(item)        

        if len(materials_to_remove) == 0 and len(materials_to_add) == 0:
            return False,[],[]

        return True,materials_to_remove,materials_to_add
