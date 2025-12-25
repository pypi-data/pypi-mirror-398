import requests,json

class GitHandler:
    def get_git_account_name_by_id(self, app_id, git_provider_id):
        """
        Get git account name by git provider ID for a given app.
        Args:
            app_id (int): Application ID
            git_provider_id (int): Git provider ID
        Returns:
            dict: Result with success status and git account name or error message
        """
        try:
            response = requests.get(
                f"{self.base_url}/orchestrator/app/{app_id}/autocomplete/git",
                headers=self.headers
            )
            if response.status_code == 200:
                result = response.json()
                git_accounts = result.get("result", [])
                for account in git_accounts:
                    if account.get("id") == git_provider_id:
                        return {"success": True, "git_account_name": account.get("name")}
                return {"success": False, "error": f"Could not find git account with id {git_provider_id}"}
            else:
                return {"success": False, "error": f"Failed to fetch git accounts: {response.text}"}
        except Exception as e:
            return {"success": False, "error": f"Exception occurred: {str(e)}"}
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
    def get_git_provider_id_by_name(self, git_account_name):
        """
        Get git provider ID by git account name from Devtron.
        
        Args:
            git_account_name (str): Name of the git account
            
        Returns:
            dict: Result with success status and git provider ID or error message
        """
        try:
            # Make API call to get all git providers
            response = requests.get(
                f'{self.base_url}/orchestrator/git/provider',
                headers=self.headers
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                # Find the git provider with the matching name
                git_providers = result.get('result', [])
                for provider in git_providers:
                    if provider.get('name') == git_account_name:
                        return {
                            'success': True,
                            'git_provider_id': provider.get('id')
                        }
                
                # If we didn't find a matching git provider
                return {
                    'success': False,
                    'error': f'Could not find git provider with name {git_account_name}'
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
    def add_git_material(self, config_data):
        """
        Add git material to an application in Devtron.
        
        Args:
            config_data (dict): Configuration data from YAML file
            
        Returns:
            dict: Result of the operation with success status and material details or error message
        """
        try:
            # Extract git material details from config
            app_id = config_data.get('app_id')
            git_repositories = config_data.get('git_repositories', [])
            
            if not app_id:
                return {
                    'success': False,
                    'error': 'app_id is required'
                }
            
            if not git_repositories:
                return {
                    'success': False,
                    'error': 'At least one git repository is required'
                }
            
            # Validate checkout paths for multiple repositories
            if len(git_repositories) > 1:
                checkout_paths = []
                empty_path_count = 0
                
                for repo in git_repositories:
                    checkout_path = repo.get('checkout_path', '')
                    if not checkout_path or checkout_path == './':
                        empty_path_count += 1
                    else:
                        checkout_paths.append(checkout_path)
                
                # Check if more than one repository has empty checkout path
                if empty_path_count > 1:
                    return {
                        'success': False,
                        'error': 'Only one git repository can have an empty or default (./) checkout path when multiple repositories are provided'
                    }
                
                # Check for duplicate checkout paths
                if len(checkout_paths) != len(set(checkout_paths)):
                    return {
                        'success': False,
                        'error': 'All git repositories must have unique checkout paths'
                    }
            
            # Process each git repository individually
            all_materials = []
            for i, repo in enumerate(git_repositories):
                url = repo.get('url')
                git_account_name = repo.get('git_account_name')
                checkout_path = repo.get('checkout_path', './')  # Default to './' if not provided
                fetch_submodules = repo.get('fetch_submodules', False)
                filter_pattern = repo.get('filter_pattern', [])
                
                if not url:
                    return {
                        'success': False,
                        'error': 'URL is required for each git repository'
                    }
                
                if not git_account_name:
                    return {
                        'success': False,
                        'error': 'git_account_name is required for each git repository'
                    }
                
                print(f"Saving git repository {i+1}/{len(git_repositories)} with URL: {url}")
                
                # Get git provider ID from git account name
                provider_result = self.get_git_provider_id_by_name(git_account_name)
                if not provider_result['success']:
                    return {
                        'success': False,
                        'error': f'Could not get git provider ID for account {git_account_name}: {provider_result["error"]}'
                    }
                
                git_provider_id = provider_result['git_provider_id']
                
                # Prepare material for this repository
                material = {
                    'url': url,
                    'checkoutPath': checkout_path,
                    'gitProviderId': git_provider_id,
                    'fetchSubmodules': fetch_submodules,
                    'filterPattern': filter_pattern
                }
                
                # Prepare payload for adding this git material
                payload = {
                    'appId': app_id,
                    'material': [material]  # Send one repository at a time
                }
                
                # Make API call to add git material
                response = requests.post(
                    f'{self.base_url}/orchestrator/app/material',
                    headers=self.headers,
                    data=json.dumps(payload)
                )
                
                # Check response status
                if response.status_code == 200:
                    result = response.json()
                    materials = result.get('result', {}).get('material', [])
                    if materials:
                        all_materials.extend(materials)
                        print(f"Successfully saved git repository with URL: {url}")
                    else:
                        return {
                            'success': False,
                            'error': f'No material returned for repository {url}'
                        }
                else:
                    # Handle error response
                    try:
                        error_result = response.json()
                        error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                        if error_message:
                            return {
                                'success': False,
                                'error': f'API request failed for repository {url}: {error_message}'
                            }
                        else:
                            return {
                                'success': False,
                                'error': f'API request failed for repository {url} with status {response.status_code}: {response.text}'
                            }
                    except:
                        # If we can't parse the error response, return the raw error
                        return {
                            'success': False,
                            'error': f'API request failed for repository {url} with status {response.status_code}: {response.text}'
                        }
            
            return {
                'success': True,
                'materials': all_materials
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }        
    def get_current_git_materials(self, app_id):
        """
        Fetch and return the current git materials for a given application ID.
        Args:
            app_id (int): The ID of the application
        Returns:
            dict: Result with success status and list of materials or error message
        """
        try:
            response = requests.get(
                f"{self.base_url}/orchestrator/app/get/{app_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                result = response.json()
                materials = result.get("result", {}).get("material", [])
                return {
                    "success": True,
                    "materials": materials
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
