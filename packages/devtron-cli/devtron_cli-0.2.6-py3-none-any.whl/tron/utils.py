import requests,base64
import json
import yaml
from deepdiff import DeepDiff


class DevtronUtils:
    def get_app_description_from_metadata(self, app_id):
        """
        Fetch app metadata and return the description field from /orchestrator/app/meta/info/{app_id}
        Args:
            app_id (int or str): Application ID
        Returns:
            str: Description if found, else empty string
        """
        try:
            url = f"{self.base_url}/orchestrator/app/meta/info/{app_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})
                desc = result.get("description")
                if not desc and "note" in result and isinstance(result["note"], dict):
                    desc = result["note"].get("description", "")
                return desc or ""
            else:
                return ""
        except Exception:
            return ""
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers

    def makebase64(self, secret):
        """
        UTF-8 encoding is required because the base64.b64encode() function expects bytes, not a Python string. Encoding a string with .encode('utf-8') converts it to bytes, which can then be base64-encoded.
        """
        if not secret or not isinstance(secret, dict):
            return None
        new_secret = dict(secret)
        data = new_secret.get('data', {})
        if not isinstance(data, dict):
            return new_secret
        encoded_data = {}
        for k, v in data.items():
            encoded_data[k] = base64.b64encode(str(v).encode('utf-8')).decode('utf-8')
        new_secret['data'] = encoded_data
        return new_secret

    def get_team_id_by_project_name(self, project_name):
        """
        Get team ID by project name from Devtron.
        
        Args:
            project_name (str): Name of the project
            
        Returns:
            dict: Result with success status and team ID or error message
        """
        try:
            # Make API call to get all teams
            response = requests.get(
                f'{self.base_url}/orchestrator/team',
                headers=self.headers
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                # Find the team with the matching name
                teams = result.get('result', [])
                for team in teams:
                    if team.get('name') == project_name:
                        return {
                            'success': True,
                            'team_id': team.get('id')
                        }
                
                # If we didn't find a matching team
                return {
                    'success': False,
                    'error': f'Could not find team with name {project_name}'
                }
            else:
                # Handle error response
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {
                            'success': False,
                            'error': f'API request failed: {error_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'API request failed with status {response.status_code}: {response.text}'
                        }
                except Exception as e:
                    # If we can't parse the error response, return the raw error
                    return {
                        'success': False,
                        'error': f'API request failed with status {response.status_code}: {response.text}'
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    @staticmethod
    def remove_empty_values(obj):
        """
        Recursively remove empty values from a dictionary or list.
        Removes keys with empty strings, None, empty dicts, empty lists, etc.
        """
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                cleaned_value = DevtronUtils.remove_empty_values(v)
                # Only include non-empty values
                if cleaned_value is not None and cleaned_value != '' and cleaned_value != {} and cleaned_value != []:
                    result[k] = cleaned_value
            return result if result else None
            
        elif isinstance(obj, list):
            result = []
            for item in obj:
                cleaned_item = DevtronUtils.remove_empty_values(item)
                # Only include non-empty items
                if cleaned_item is not None and cleaned_item != '' and cleaned_item != {} and cleaned_item != []:
                    result.append(cleaned_item)
            return result if result else None
            
        else:
            # Return primitive values as-is
            return obj

    def _get_chart_details_from_id(self, app_id, chart_ref_id):
        """Get chart name from chart reference ID"""
        try:
            url = f"{self.base_url}/orchestrator/chartref/autocomplete/{app_id}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                result = response.json().get('result', {})
                chart_refs = result.get('chartRefs', [])
                for chart_ref in chart_refs:
                    if chart_ref.get('id') == chart_ref_id:
                        return chart_ref
            return None
        except Exception as e:
            print(f"Warning: Could not fetch chart name: {str(e)}")
            return None
        
    def get_application_id_by_name(self,app_name):


        """
        Get application ID by application name from Devtron.
        
        Args:
            app_name (str): Name of the application
            
        Returns:
            dict: Result with success status and app ID or error message
        """
        try:
            # Make API call to get all applications
            response = requests.get(
                f'{self.base_url}/orchestrator/app/autocomplete',
                headers=self.headers
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()

                # Find the application with the matching name
                apps = result.get('result', [])
                for app in apps:
                    if app.get('name') == app_name:
                        return {
                            'success': True,
                            'app_id': app.get('id')
                        }
                
                # If we didn't find a matching application
                return {
                    'success': False,
                    'error': f'Could not find application with name {app_name}'
                }
            else:
                # Handle error response
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {
                            'success': False,
                            'error': f'API request failed: {error_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'API request failed with status {response.status_code}: {response.text}'
                        }
                except:
                    # If we can't parse the error response, return the raw error
                    return {
                        'success': False,
                        'error': f'API request failed with status {response.status_code}: {response.text}'
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def get_cd_pipeline_id_by_environment_name(self, app_id, environment_name):
        """
        Get CD pipeline ID by environment name from Devtron.
        
        Args:
            app_id (int): The ID of the application
            environment_name (str): Name of the environment
            
        Returns:
            dict: Result with success status and CD pipeline ID or error message
        """
        try:
            # Make API call to get all CD pipelines for the application
            response = requests.get(
                f'{self.base_url}/orchestrator/app/cd-pipeline/{app_id}',
                headers=self.headers
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                # Find the CD pipeline with the matching environment name
                pipelines = result.get('result', {}).get('pipelines', [])
                for pipeline in pipelines:
                    if pipeline.get('environmentName') == environment_name:
                        return {
                            'success': True,
                            'pipeline_id': pipeline.get('id')
                        }
                
                # If we didn't find a matching CD pipeline
                return {
                    'success': False,
                    'error': f'Could not find CD pipeline with environment name {environment_name}'
                }
            else:
                # Handle error response
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {
                            'success': False,
                            'error': f'API request failed: {error_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'API request failed with status {response.status_code}: {response.text}'
                        }
                except:
                    # If we can't parse the error response, return the raw error
                    return {
                        'success': False,
                        'error': f'API request failed with status {response.status_code}: {response.text}'
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    @staticmethod
    def convert_dict_to_yaml(data: dict, indent: int = 0) -> str:
        """Convert a dictionary to a YAML string representation."""
        yaml_str = ""
        for key, value in data.items():
            indentation = "  " * indent
            if isinstance(value, dict):
                yaml_str += f"{indentation}{key}:\n"
                yaml_str += DevtronUtils.convert_dict_to_yaml(value, indent + 1)
            elif isinstance(value, list):
                yaml_str += f"{indentation}{key}:\n"
                for item in value:
                    if isinstance(item, dict):
                        yaml_str += f"{indentation}  - "
                        # Handle nested dict in list
                        item_yaml = DevtronUtils.convert_dict_to_yaml(item, indent + 2).strip()
                        yaml_str += item_yaml.replace('\n', '\n  ') + '\n'
                    else:
                        yaml_str += f"{indentation}  - {item}\n"
            else:
                yaml_str += f"{indentation}{key}: {value}\n"
        return yaml_str
        
        return yaml.dump(data, indent=indent, default_flow_style=False)
    def get_application_details(self, app_id):
        """
        Fetch application details by app ID.

        Args:
            app_id (int): The ID of the application

        Returns:
            dict: Result with success status, Git Material IDs, and full application data
        """
        try:
            print(f"Fetching details for application ID: {app_id}")
            response = requests.get(
                f"{self.base_url}/orchestrator/app/get/{app_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                materials = result.get("result", {}).get("material", [])
                material_ids = [material.get("id") for material in materials]
                print(f"Git Material IDs: {material_ids}")
                return {
                    "success": True,
                    "material_ids": material_ids,
                    "data": result.get("result", {})
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch application details: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }

    def get_workflows(self, app_id):
        """
        Fetch all workflows for an application by app ID.

        Args:
            app_id (int): The ID of the application

        Returns:
            dict: Result with success status and workflows data or error message
        """
        try:
            print(f"Fetching workflows for application ID: {app_id}")
            response = requests.get(
                f"{self.base_url}/orchestrator/app/app-wf/{app_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                workflows = result.get("result", {}).get("workflows", [])
                print(f"Found {len(workflows)} workflows")
                return {
                    "success": True,
                    "workflows": workflows
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch workflows: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }

    def get_ci_pipelines(self, app_id):
        """
        Fetch all CI pipelines for an application by app ID.

        Args:
            app_id (int): The ID of the application

        Returns:
            dict: Result with success status and CI pipelines data or error message
        """
        try:
            print(f"Fetching CI pipelines for application ID: {app_id}")
            response = requests.get(
                f"{self.base_url}/orchestrator/app/ci-pipeline/{app_id}",
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                ci_pipelines = result.get("result", {}).get("ciPipelines", [])
                print(f"Found {len(ci_pipelines)} CI pipelines")
                return {
                    "success": True,
                    "ci_pipelines": ci_pipelines
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to fetch CI pipelines: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }
    def get_container_registry_id_by_name(self, registry_name):
        """
        Get container registry ID by registry name from Devtron.
        Args:
            registry_name (str): Name of the container registry
        Returns:
            dict: Result with success status and registry ID or error message
        """
        try:
            response = requests.get(
                f'{self.base_url}/orchestrator/docker/registry',
                headers=self.headers
            )
            if response.status_code == 200:
                result = response.json()
                registries = result.get('result', [])
                for registry in registries:
                    if registry.get('id') == registry_name:
                        return {
                            'success': True,
                            'registry_id': registry.get('id')
                        }
                return {
                    'success': False,
                    'error': f'Could not find container registry with name {registry_name}'
                }
            else:
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {
                            'success': False,
                            'error': f'API request failed: {error_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'API request failed with status {response.status_code}: {response.text}'
                        }
                except:
                    return {
                        'success': False,
                        'error': f'API request failed with status {response.status_code}: {response.text}'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def get_ci_pipeline_id_by_name(self, app_id, pipeline_name):
        """
        Get CI pipeline ID by pipeline name from Devtron.
        
        Args:
            app_id (int): The ID of the application
            pipeline_name (str): Name of the CI pipeline
            
        Returns:
            dict: Result with success status and CI pipeline ID or error message
        """
        try:
            ci_pipelines_result = self.get_ci_pipelines(app_id)
            if not ci_pipelines_result['success']:
                return ci_pipelines_result
                
            ci_pipelines = ci_pipelines_result['ci_pipelines']
            for pipeline in ci_pipelines:
                if pipeline.get('name') == pipeline_name:
                    return {
                        'success': True,
                        'ci_pipeline_id': pipeline.get('id')
                    }
            
            return {
                'success': False,
                'error': f'Could not find CI pipeline with name {pipeline_name}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def get_ci_pipeline_details(self, app_id, ci_pipeline_id):
        """
        Get detailed information about a specific CI pipeline.
        
        Args:
            app_id (int): The ID of the application
            ci_pipeline_id (int): The ID of the CI pipeline
            
        Returns:
            dict: Result with success status and CI pipeline details or error message
        """
        try:
            response = requests.get(
                f'{self.base_url}/orchestrator/app/ci-pipeline/{app_id}/{ci_pipeline_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'pipeline_details': result.get('result', {})
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch CI pipeline details: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    @staticmethod
    def compare_dicts(dict1, dict2):
        """
        Compare two dictionaries and return the differences.

        Args:
            dict1 (dict): First dictionary
            dict2 (dict): Second dictionary

        Returns:
            dict: {
                'success': bool,
                'is_differ': bool,
                'differences': str (YAML string with differences)
            }
        """
        try:
            diff = DeepDiff(dict1 or {}, dict2 or {}, ignore_order=True).to_dict()

            if diff:
                return {
                    "success": True,
                    "is_differ": True,
                    "differences": diff
                }
            else:
                return {
                    "success": True,
                    "is_differ": False,
                    "differences": None
                }

        except Exception as e:
            return {
                "success": False,
                "is_differ": False,
                "error": f"Error: {str(e)}"
            }



    def get_cd_pipeline_details(self, app_id, cd_pipeline_id):
        """
        Get detailed information about a specific CD pipeline.
        
        Args:
            app_id (int): The ID of the application
            cd_pipeline_id (int): The ID of the CD pipeline
            
        Returns:
            dict: Result with success status and CD pipeline details or error message
        """
        try:
            response = requests.get(
                f'{self.base_url}/orchestrator/app/v2/cd-pipeline/{app_id}/{cd_pipeline_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'pipeline_details': result.get('result', {})
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to fetch CD pipeline details: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    @staticmethod
    def get_plugin_details_by_id(base_url, headers, plugin_ids, app_id) -> dict:
        try:
            url = f"{base_url}/orchestrator/plugin/global/list/detail/v2"
            payload = {
                "appId": app_id,
                "parentPluginIds": [],
                "pluginIds": plugin_ids
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code != 200:
                return{
                    'success': False,
                    "error": "Not able to fetch the plugin details"

                }
            response = response.json()
            result = response.get("result", {})
            return {
                "success": True,
                "plugin_data": result
            }

        except Exception as e:
            return {
                'success': False,
                "error": str(e)
            }

    @staticmethod
    def get_wf_id_from_cd_id(base_url, headers, ci_id, app_id):
        try:
            url = f"{base_url}/orchestrator/app/app-wf/{app_id}"

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": "Failed to get wf ID"
                }
            result = response.json().get("result", {})
            for wf in result.get("workflows", []):
                for node in wf.get("tree", []):
                    if node.get("componentId", 0) == ci_id:
                        return {
                            "success": True,
                            "wf_id": node.get("appWorkflowId")
                        }
            return {
                "success": False,
                "error": "Workflow not found for given CI"
            }


        except Exception as e:
            return {
                "success": False,
                "error": "Failed to get wf ID"
            }

    @staticmethod
    def get_plugin_details_by_name(base_url, headers, plugin_name: str) -> dict:
        import re
        try:
            new_plugin_name = plugin_name.replace(" ", "+")
            api_url = f"{base_url.rstrip('/')}/orchestrator/plugin/global/list/v2?searchKey={new_plugin_name}&offset=0"
            response = requests.get(api_url, headers=headers)
            data = response.json()
            status_code = data.get("code", 0)
            if status_code == 200:
                plugin_search_result = data.get("result", {})
                if plugin_search_result:
                    plugin_list = plugin_search_result.get("parentPlugins", [])
                    pattern = re.compile(rf"^{re.escape(plugin_name)}(\s+[vV]\d.*)?$")
                    for plugin in plugin_list:
                        name = plugin.get("name", "")
                        if pattern.match(name):
                            return {'success': True, 'plugin': plugin}
                        elif name == plugin_name:
                            return {'success': True, 'plugin': plugin}
                # Plugin not found
                return {'success': False, 'error': f'Plugin "{plugin_name}" not found in available plugins'}
            else:
                return {'success': False, 'error': f'API request failed with status code {status_code}: {data.get("errors", "Unknown error")}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}


    @staticmethod

    def get_cd_pipelines(base_url, headers, app_id):
        try:
            url = f"{base_url}/orchestrator/app/cd-pipeline/{app_id}"
            response = requests.get(url, headers=headers)
            if not response.status_code == 200:
                return {
                    "success": False,
                    "error": "Failed to get CD Pipelines"
                }
            result = response.json().get("result", {})
            return {
                "success": True,
                "cd_pipelines": result.get("pipelines", [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }

  
    @staticmethod
    def get_env_id(base_url, headers, environment_name):
        try:
            print(f"Getting environment ID for: {environment_name}")
            response = requests.get(f'{base_url}/orchestrator/env/autocomplete', headers=headers)
            if response.status_code == 200:
                environments = response.json().get('result', [])
                for e in environments:
                    if e.get("environment_name") == environment_name:
                        return {
                            'success': True,
                            'environment_id': e.get("id"),
                            'namespace': e.get("namespace")
                        }
                return {'success': False, 'error': f'Environment "{environment_name}" not found'}
            return {'success': False, 'error': f'API request failed: {response.status_code} {response.text}'}
        except Exception as e:
            return {'success': False, 'error': f'Exception occurred: {str(e)}'}

# --- YAML utilities for multi-line string handling ---

class CustomDumper(yaml.SafeDumper):
    """Custom YAML dumper that handles multi-line strings properly."""
    
    def choose_scalar_style(self):
        """
        Override the style selection to respect our literal presenter.
        This ensures multi-line strings are output with pipe (|) style.
        """
        if self.event.value and '\n' in self.event.value:
            if self.event.style == '|':
                return '|'
        return super().choose_scalar_style()


def literal_presenter(dumper, data):
    """
    Represent strings with newlines as literal blocks (pipe | style).
    Single-line strings are represented normally.
    """
    if isinstance(data, str) and '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


# Register the literal presenter with the CustomDumper
CustomDumper.add_representer(str, literal_presenter)


def dump_yaml(data, stream=None, **kwargs):
    """
    Dump data to YAML using CustomDumper with sensible defaults.
    
    Args:
        data: The data to serialize to YAML
        stream: Optional file-like object to write to
        **kwargs: Additional arguments to pass to yaml.dump()
    
    Returns:
        str if stream is None, otherwise None
    """
    defaults = {
        'Dumper': CustomDumper,
        'default_flow_style': False,
        'allow_unicode': True,
        'sort_keys': False,
        'width': float("inf")
    }
    # Merge provided kwargs with defaults (provided kwargs take precedence)
    merged_kwargs = {**defaults, **kwargs}
    
    return yaml.dump(data, stream=stream, **merged_kwargs)
