
import requests,json
from tron.utils import DevtronUtils

class BuildConfig:
    def __init__(self, base_url, headers):
        self.base_url = base_url
        self.headers = headers
        self.devtron_utils = DevtronUtils(base_url, headers)

    def create_pipeline(self, config_data):
        """
        Create a new pipeline for an application.
        
        Args:
            config_data (dict): Configuration data from YAML file
            
        Returns:
            dict: Result of the operation with success status and pipeline ID or error message
        """
        try:
            print("Creating pipeline...")
            
            # Extract pipeline details from config
            app_id = config_data.get('app_id')
            pipeline_name = config_data.get('pipeline', {}).get('name')
            
            if not app_id or not pipeline_name:
                return {
                    'success': False,
                    'error': 'app_id and pipeline.name are required'
                }
            
            # Prepare payload for pipeline creation
            payload = {
                'appId': app_id,
                'name': pipeline_name,
                'ciPipeline': config_data.get('pipeline', {}).get('ci_config', {})
            }
            
            # Make API call to create pipeline
            print(f"Creating pipeline: {pipeline_name}")
            response = requests.post(
                f'{self.base_url}/app/pipeline',
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                pipeline_id = result.get('id')
                print(f"Pipeline created successfully with ID: {pipeline_id}")
                return {
                    'success': True,
                    'pipeline_id': pipeline_id
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
    def configure_ci_pipeline(self, app_id, git_material_id, config_data):
        registry_name = config_data.get('build_configurations', {}).get('container_registry_name')
        registry_result = self.devtron_utils.get_container_registry_id_by_name(registry_name)
        if not registry_result['success']:
            print(f"Error getting registry ID: {registry_result['error']}")
            return {'success': False, 'error': registry_result['error']}
        registry_id = registry_result['registry_id']
        print(f"Found registry ID: {registry_id}")
        target_platform = config_data.get('build_configurations', {}).get('target_platform', "")

        repository_name = config_data.get('build_configurations', {}).get('repository_name')
        print(f"Repository name: {repository_name}")
        build_type = config_data.get('build_configurations', {}).get('build_type')
        print(f"Performing operation for build_type: {build_type}")
        build_context = config_data.get('build_context', {}).get('build_context', '')
        docker_build_args_raw = config_data.get('build_configurations', {}).get('docker_build_args', {})
        # Convert keys to uppercase and values to string for API contract
        docker_build_args = {str(k): str(v) for k, v in docker_build_args_raw.items()}
        dockerfile_path = config_data.get('build_configurations', {}).get('dockerfile_path', './Dockerfile')
        dockerfile_content = config_data.get('build_configurations', {}).get('dockerfile_content')
        dockerfile_repository = config_data.get('build_configurations', {}).get('dockerfile_repository', '')
        try:
            print(f"Configuring Build Config for application ID: {app_id}")

            if build_type == "DockerfileExists":
                payload = {
                    "id": None,
                    "appId": app_id,
                    "dockerRegistry": registry_name,
                    "dockerRepository": repository_name,
                    "beforeDockerBuild": [],
                    "ciBuildConfig": {
                        "buildPackConfig": None,
                        "ciBuildType": "self-dockerfile-build",
                        "dockerBuildConfig": {
                            "dockerfileRelativePath": dockerfile_path,
                            "dockerfileContent": dockerfile_content if dockerfile_content else "",
                            "targetPlatform": target_platform,
                            "buildContext": build_context,
                            "dockerfilePath": dockerfile_path,
                            "args": docker_build_args,
                            "dockerfileRepository": dockerfile_repository
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": git_material_id,
                        "useRootBuildContext": True
                    },
                    "afterDockerBuild": [],
                    "appName": ""
                }
            elif build_type == "CreateDockerfile":
                payload = {
                    "id": None,
                    "appId": app_id,
                    "dockerRegistry": registry_name,
                    "dockerRepository": repository_name,
                    "beforeDockerBuild": [],
                    "ciBuildConfig": {
                        "buildPackConfig": None,
                        "ciBuildType": "managed-dockerfile-build",
                        "dockerBuildConfig": {
                            "dockerfileRelativePath": dockerfile_path,
                            "dockerfileContent": dockerfile_content if dockerfile_content else "",
                            "language": config_data.get('build_configurations', {}).get('language', ""),
                            "languageFramework": config_data.get('build_configurations', {}).get('language_framework', ""),
                            "dockerfilePath": dockerfile_path,
                            "args": docker_build_args,
                            "dockerfileRepository": dockerfile_repository,
                            "targetPlatform": target_platform
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": git_material_id,
                        "useRootBuildContext": True
                    },
                    "afterDockerBuild": [],
                    "appName": ""
                }
            elif build_type == "Buildpacks":
                payload = {
                    "id": None,
                    "appId": app_id,
                    "dockerRegistry": registry_name,
                    "dockerRepository": repository_name,
                    "beforeDockerBuild": [],
                    "ciBuildConfig": {
                        "buildPackConfig": {
                            "builderId": config_data.get('build_configurations', {}).get('builder_image', "gcr.io/buildpacks/builder:v1"),
                            "language": config_data.get('build_configurations', {}).get('language', ""),
                            "languageVersion": config_data.get('build_configurations', {}).get('version', ""),
                            "projectPath": config_data.get('build_configurations', {}).get('build_context', "./"),
                            "args": docker_build_args
                        },
                        "ciBuildType": "buildpack-build",
                        "dockerBuildConfig": {
                            "dockerfileRelativePath": dockerfile_path,
                            "dockerfileContent": ""
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": git_material_id,
                        "useRootBuildContext": True
                    },
                    "afterDockerBuild": [],
                    "appName": ""
                }

            # Add more build_type conditions here as needed

            response = requests.post(
                f"{self.base_url}/orchestrator/app/ci-pipeline",
                headers=self.headers,
                data=json.dumps(payload)
            )

            if response.status_code == 200:
                result = response.json()
                print("Buildconfiguration saved successfully.")
                return {
                    "success": True,
                    "data": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to configure CI pipeline: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }
