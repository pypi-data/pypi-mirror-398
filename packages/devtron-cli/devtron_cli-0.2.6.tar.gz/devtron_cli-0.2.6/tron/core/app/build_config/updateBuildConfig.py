import requests,json
from tron.utils import DevtronUtils

class UpdateBuildConfig:
    def __init__(self, base_url, headers, gitHandler):
        self.base_url = base_url
        self.headers = headers
        self.devtron_utils = DevtronUtils(base_url, headers)
        self.gitHandler = gitHandler
    def update_container_registry(self, config_data):
        # Extract container registry details from config
        app_result = self.devtron_utils.get_application_id_by_name(config_data.get('app_name'))
        if not app_result['success']:
            print(f"Error getting application ID: {app_result['error']}")
            return {'success': False, 'error': app_result['error']}
        app_id = app_result['app_id']
        print("Updating application build configuration...")
        registry_name = config_data.get('build_configurations', {}).get('container_registry_name')
        registry_result = self.devtron_utils.get_container_registry_id_by_name(registry_name)
        if not registry_result['success']:
            print(f"Error getting registry ID: {registry_result['error']}")
            return {'success': False, 'error': registry_result['error']}
        registry_id = registry_result['registry_id']
        repository_name = config_data.get('build_configurations', {}).get('repository_name')
        build_type = config_data.get('build_configurations', {}).get('build_type')
        build_context = config_data.get('build_context', {}).get('build_context', '')
        docker_build_args_raw = config_data.get('build_configurations', {}).get('docker_build_args', {})
        docker_build_args = {str(k): str(v) for k, v in docker_build_args_raw.items()}
        ci_pipeline_id = None
        git_material_id = None
        buildContextGitMaterialId = None
        try:
            ci_pipeline_resp = requests.get(
                f"{self.base_url}/orchestrator/app/ci-pipeline/{app_id}",
                headers=self.headers
            )
            if ci_pipeline_resp.status_code == 200:
                pipeline_data = ci_pipeline_resp.json().get('result', {})
                ci_pipeline_id = pipeline_data.get('id')
            else:
                print(f"Failed to fetch pipeline info: {ci_pipeline_resp.text}")
        except Exception as e:
            print(f"Exception while fetching pipeline info: {str(e)}")
        use_root_build_context = config_data.get('build_configurations', {}).get('use_root_build_context', True)
        build_context = config_data.get('build_configurations', {}).get('build_context', './')
        target_platform = config_data.get('build_configurations', {}).get('target_platform', "linux/amd64,linux/arm64")
        dockerfile_path = config_data.get('build_configurations', {}).get('dockerfile_path', './Dockerfile')
        dockerfile_content = config_data.get('build_configurations', {}).get('dockerfile_content')
        dockerfile_repository = config_data.get('build_configurations', {}).get('dockerfile_repository', '')

        git_material_id = self.get_git_material_id_from_name(app_id, config_data.get('build_configurations', {}).get('dockerfile_repository'))
        buildContextGitMaterialId = self.get_git_material_id_from_name(app_id, config_data.get('build_configurations', {}).get('build_context_repository'))

        checkIfdiffbuildconfig=self.checkIfdiffbuildconfig(config_data.get('build_configurations', {}),ci_pipeline_resp.json().get('result', {}))
        if not checkIfdiffbuildconfig:
            print("No changes detected,skipping build configuration update.")
            return {"success": True, "message": "No changes detected in build configuration.,skipping update."}
            # Build payload based on build_type
        else:
            if build_type == "DockerfileExists":
                print("Preparing payload for build_type: Dockerfile")
                payload = {
                    "id": ci_pipeline_id,
                    "appId": app_id,
                    "dockerRegistry": registry_id,
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
                            "args": docker_build_args
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": buildContextGitMaterialId,
                        "useRootBuildContext": use_root_build_context
                    },
                    "afterDockerBuild": [],
                    "appName": config_data.get('app_name', "")
                }
            elif build_type == "CreateDockerfile":
                print("Preparing payload for build_type: CreateDockerfile")
                dockerfile_content = config_data.get('build_configurations', {}).get('dockerfile_content', '')
                language = config_data.get('build_configurations', {}).get('language', '')
                language_framework = config_data.get('build_configurations', {}).get('language_framework', '')
                use_buildx = config_data.get('build_configurations', {}).get('use_buildx', False)
                dockerfile_path = config_data.get('build_configurations', {}).get('dockerfile_path', './Dockerfile')
                payload = {
                    "id": ci_pipeline_id,
                    "appId": app_id,
                    "dockerRegistry": registry_id,
                    "dockerRepository": repository_name,
                    "beforeDockerBuild": [],
                    "ciBuildConfig": {
                        "buildPackConfig": None,
                        "ciBuildType": "managed-dockerfile-build",
                        "dockerBuildConfig": {
                            "dockerfileRelativePath": dockerfile_path,
                            "dockerfileContent": dockerfile_content,
                            "targetPlatform": target_platform,
                            "useBuildx": use_buildx,
                            "language": language,
                            "languageFramework": language_framework,
                            "dockerfilePath": f"./{dockerfile_path}",
                            "buildContext": build_context,
                            "args": docker_build_args
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": buildContextGitMaterialId,
                        "useRootBuildContext": use_root_build_context
                    },
                    "afterDockerBuild": [],
                    "appName": config_data.get('app_name', "")
                }
            elif build_type == "Buildpacks":
                print("Preparing payload for build_type: BuilderImage (buildpack-build)")
                builder_image = config_data.get('build_configurations', {}).get('builder_image', 'gcr.io/buildpacks/builder:v1')
                language = config_data.get('build_configurations', {}).get('language', 'Java')
                version = config_data.get('build_configurations', {}).get('version', 'Autodetect')
                project_path = config_data.get('build_configurations', {}).get('build_context', './')
                payload = {
                    "id": ci_pipeline_id,
                    "appId": app_id,
                    "dockerRegistry": registry_id,
                    "dockerRepository": repository_name,
                    "beforeDockerBuild": [],
                    "ciBuildConfig": {
                        "buildPackConfig": {
                            "builderId": builder_image,
                            "language": language,
                            "languageVersion": version,
                            "projectPath": project_path,
                            "args": docker_build_args,
                            "projectPath": project_path
                        },
                        "ciBuildType": "buildpack-build",
                        "dockerBuildConfig": {
                            "dockerfileRelativePath": dockerfile_path,
                            "dockerfileContent": dockerfile_content if dockerfile_content else ""
                        },
                        "gitMaterialId": git_material_id,
                        "buildContextGitMaterialId": buildContextGitMaterialId,
                        "useRootBuildContext": use_root_build_context
                    },
                    "afterDockerBuild": [],
                    "appName": config_data.get('app_name', "")
                }
            else:
                return {"success": False, "error": f"Unsupported build_type: {build_type}"}
        try:
            response = requests.post(
                f"{self.base_url}/orchestrator/app/ci-pipeline/template/patch",
                headers=self.headers,
                data=json.dumps(payload)
            )
            if response.status_code == 200:
                print(f"Container registry updated successfully!")
                return {"success": True, "message": "Container registry updated successfully!"}
            else:
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {"success": False, "error": f"API request failed: {error_message}"}
                    else:
                        return {"success": False, "error": f"API request failed with status {response.status_code}: {response.text}"}
                except:
                    return {"success": False, "error": f"API request failed with status {response.status_code}: {response.text}"}
        except Exception as e:
            return {"success": False, "error": f"Exception occurred: {str(e)}"}
    def checkIfdiffbuildconfig(self,build_configurations,pipeline_data):
        diff_found= False
        # print("build_configurations:", build_configurations)
        # print("pipeline_data:", pipeline_data)
        
        # checking each field one by one

        # compare dockerfile_repository with git material id 
        get_repo_name = self.get_git_repo_name_from_id(pipeline_data.get('appId'), pipeline_data.get('ciBuildConfig', {}).get('gitMaterialId'))
        if build_configurations.get('dockerfile_repository') != get_repo_name:
            print("Dockerfile repository is different.")
            diff_found = True

        # Early return if build types match
        if build_configurations.get('build_type') == "Buildpacks" and pipeline_data.get('ciBuildConfig', {}).get('ciBuildType') == "buildpack-build":
            return diff_found

        if build_configurations.get('build_type') == "DockerfileExists" and pipeline_data.get('ciBuildConfig', {}).get('ciBuildType') != "self-dockerfile-build":
            print("Build type is different.")
            if build_configurations.get('dockerfile_path') != pipeline_data.get('ciBuildConfig', {}).get('dockerBuildConfig', {}).get('dockerfileRelativePath'):
                print("Dockerfile path is different.")
            diff_found = True

            diff_found = True
        if build_configurations.get('build_type') == "CreateDockerfile" and pipeline_data.get('ciBuildConfig', {}).get('ciBuildType') != "managed-dockerfile-build":
            print("Build type is different.")
            diff_found = True
            
        if build_configurations.get('build_type') == "Buildpacks" and pipeline_data.get('ciBuildConfig', {}).get('ciBuildType') != "buildpack-build":
            print("Build type is different.")
            diff_found = True
            return diff_found

        if build_configurations.get('container_registry_name') != pipeline_data.get('dockerRegistry'):
            print("Container registry name is different.")
            diff_found = True
        if build_configurations.get('repository_name') != pipeline_data.get('dockerRepository'):
            print("Repository name is different.")
            diff_found = True

        if build_configurations.get('docker_build_args') != pipeline_data.get('ciBuildConfig', {}).get('dockerBuildConfig', {}).get('args', {}):
            print("Docker build args are different.")
            diff_found = True
        if build_configurations.get('target_platform') != pipeline_data.get('ciBuildConfig', {}).get('dockerBuildConfig', {}).get('targetPlatform'):
            print("Target platforms are different.")
            diff_found = True
        if build_configurations.get('dockerfile_content') != None and build_configurations.get('dockerfile_content') != pipeline_data.get('ciBuildConfig', {}).get('dockerBuildConfig', {}).get('dockerfileContent'):
            print("Dockerfile content is different.")
            diff_found = True

        # compare build_context
        current_build_context = build_configurations.get('build_context', './')
        from_config_build_context = (
            pipeline_data
            .get('ciBuildConfig', {})
            .get('dockerBuildConfig', {})
            .get('buildContext', './')
        )

        if current_build_context != from_config_build_context:
            print("Build context is different.")
            print(current_build_context,from_config_build_context)
            diff_found = True

        # compare build_context_git_material_id with buildContextGitMaterialId
        get_repo_name = self.get_git_repo_name_from_id(pipeline_data.get('appId'), pipeline_data.get('ciBuildConfig', {}).get('buildContextGitMaterialId'))

        if build_configurations.get('build_context_repository') != get_repo_name:
            print("Build context repository is different.")
            diff_found = True


        return diff_found
    def get_git_repo_name_from_id(self, app_id, material_id):
        # Logic to get the git repository name from the git_material_id
        materials = self.gitHandler.get_current_git_materials(app_id).get('materials', [])
        for material in materials:
            if material.get('id') == material_id:
                return material['name']
    def get_git_material_id_from_name(self, app_id, repo_name):
        # Logic to get the git_material_id from the git repository name
        materials = self.gitHandler.get_current_git_materials(app_id).get('materials', [])
        for material in materials:
            if material.get('name') == repo_name:
                return material['id']
        return None