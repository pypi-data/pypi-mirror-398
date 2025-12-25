import requests
import json
import yaml
from tron.core.app import *
from tron.utils    import DevtronUtils, dump_yaml
from tron.validators import validate_labels

class DevtronApplication:
    def _normalize_custom_task(self, task):
        if not isinstance(task, dict):
            return task
        # Normalize type
        if 'type' in task:
            task['type'] = str(task['type']).lower()
        
        # Normalize script_type (if present)
        if 'script_type' in task:
            task['script_type'] = str(task['script_type']).upper()
        
        # Normalize input_variables
        if 'input_variables' in task and isinstance(task['input_variables'], list):
            for var in task['input_variables']:
                if isinstance(var, dict) and 'type' in var:
                    var['type'] = str(var['type']).upper()
        
        # Normalize output_variables (only for non-container tasks)
        if 'output_variables' in task and isinstance(task['output_variables'], list):
            for var in task['output_variables']:
                if isinstance(var, dict) and 'type' in var:
                    var['type'] = str(var['type']).upper()
        
        # Normalize conditions (only for non-container tasks)
        for cond_field in ['trigger_conditions', 'pass_conditions', 'fail_conditions']:
            if cond_field in task and isinstance(task[cond_field], list):
                for cond in task[cond_field]:
                    if isinstance(cond, dict):
                        if 'operator' in cond:
                            cond['operator'] = str(cond['operator']).strip()
                        if 'key' in cond:
                            cond['key'] = str(cond['key'])
                        if 'value' in cond:
                            cond['value'] = str(cond['value'])
        
        # Normalize container task fields
        if 'container_image' in task:
            # Ensure container_image is a string
            task['container_image'] = str(task['container_image']).strip()
            
            # Normalize command - should be string or list
            if 'command' in task:
                if isinstance(task['command'], str):
                    task['command'] = task['command'].strip()
                elif isinstance(task['command'], list):
                    task['command'] = [str(c).strip() for c in task['command']]
            
            # Normalize args - should be a list
            if 'args' in task:
                if not isinstance(task['args'], list):
                    task['args'] = [str(task['args'])]
                else:
                    task['args'] = [str(arg) for arg in task['args']]
            
            # Normalize ports_mappings - ensure proper format
            if 'ports_mappings' in task and isinstance(task['ports_mappings'], list):
                normalized_ports = []
                for port in task['ports_mappings']:
                    if isinstance(port, str):
                        # Keep string format like "8080:8090"
                        normalized_ports.append(port.strip())
                    elif isinstance(port, dict) and 'portOnLocal' in port and 'portOnContainer' in port:
                        # Convert dict to string format
                        normalized_ports.append(f"{port['portOnLocal']}:{port['portOnContainer']}")
                    elif isinstance(port, (int, float)):
                        # Single port number - use same for both
                        normalized_ports.append(f"{int(port)}:{int(port)}")
                task['ports_mappings'] = normalized_ports
            
            # Normalize directory_mappings - ensure proper format
            if 'directory_mappings' in task and isinstance(task['directory_mappings'], list):
                normalized_dirs = []
                for dir_map in task['directory_mappings']:
                    if isinstance(dir_map, str):
                        # Keep string format like "/host:/container"
                        normalized_dirs.append(dir_map.strip())
                    elif isinstance(dir_map, dict) and 'filePathOnDisk' in dir_map and 'filePathOnContainer' in dir_map:
                        # Convert dict to string format
                        normalized_dirs.append(f"{dir_map['filePathOnDisk']}:{dir_map['filePathOnContainer']}")
                task['directory_mappings'] = normalized_dirs
            
            # Normalize script_mount_path
            if 'script_mount_path' in task:
                task['script_mount_path'] = str(task['script_mount_path']).strip()
            
            # Normalize script_mount_path_on_container
            if 'script_mount_path_on_container' in task:
                task['script_mount_path_on_container'] = str(task['script_mount_path_on_container']).strip()
        
        return task

    def _normalize_tasks_section(self, section):
        if isinstance(section, dict) and 'tasks' in section and isinstance(section['tasks'], list):
            for task in section['tasks']:
                self._normalize_custom_task(task)

    def _validate_workflow_env_and_pipeline_names(self, config_data):
        """
        Validates that no environment is duplicated across all workflows and all CI/CD pipeline names are unique.
        Returns None if valid, else returns error dict.
        """
        workflows = config_data.get('workflows', [])
        env_names = set()
        duplicate_envs = set()
        ci_cd_pipeline_names = set()
        duplicate_pipeline_names = set()
        for wf in workflows:
            # CI pipeline name
            ci_name = wf.get('ci_pipeline', {}).get('name')
            if ci_name:
                if ci_name in ci_cd_pipeline_names:
                    duplicate_pipeline_names.add(ci_name)
                else:
                    ci_cd_pipeline_names.add(ci_name)
            # CD pipeline names and environments
            for cd in wf.get('cd_pipelines', []):
                env = cd.get('environment_name')
                if env:
                    if env in env_names:
                        duplicate_envs.add(env)
                    else:
                        env_names.add(env)
                cd_name = cd.get('name')
                if cd_name:
                    if cd_name in ci_cd_pipeline_names:
                        duplicate_pipeline_names.add(cd_name)
                    else:
                        ci_cd_pipeline_names.add(cd_name)
        if duplicate_envs:
            return {
                'success': False,
                'error': f'Duplicate environment(s) found across workflows: {", ".join(sorted(duplicate_envs))}'
            }
        if duplicate_pipeline_names:
            return {
                'success': False,
                'error': f'Duplicate CI/CD pipeline name(s) found across workflows: {", ".join(sorted(duplicate_pipeline_names))}'
            }
        return None

    def _validate_task_name_uniqueness(self, config_data):
        """
        Validates that task_name is unique across pre_build_configs and post_build_configs for each CI pipeline,
        and across pre_cd_configs and post_cd_configs for each CD pipeline.
        Returns None if valid, else returns error dict.
        """
        workflows = config_data.get('workflows', [])
        
        for wf_idx, workflow in enumerate(workflows):
            # Validate CI pipeline task names
            ci_pipeline = workflow.get('ci_pipeline', {})
            ci_name = ci_pipeline.get('name', f'workflow-{wf_idx + 1}')
            
            ci_task_names = set()
            ci_duplicate_tasks = set()
            
            # Collect pre_build_configs task names
            pre_build_tasks = ci_pipeline.get('pre_build_configs', {}).get('tasks', [])
            for task in pre_build_tasks:
                task_name = task.get('task_name')
                if task_name:
                    if task_name in ci_task_names:
                        ci_duplicate_tasks.add(task_name)
                    else:
                        ci_task_names.add(task_name)
            
            # Collect post_build_configs task names
            post_build_tasks = ci_pipeline.get('post_build_configs', {}).get('tasks', [])
            for task in post_build_tasks:
                task_name = task.get('task_name')
                if task_name:
                    if task_name in ci_task_names:
                        ci_duplicate_tasks.add(task_name)
                    else:
                        ci_task_names.add(task_name)
            
            if ci_duplicate_tasks:
                return {
                    'success': False,
                    'error': f'Duplicate task_name(s) found in CI pipeline "{ci_name}": {", ".join(sorted(ci_duplicate_tasks))}. Task names must be unique across pre_build_configs and post_build_configs.'
                }
            
            # Validate CD pipeline task names
            cd_pipelines = workflow.get('cd_pipelines', [])
            for cd_idx, cd_pipeline in enumerate(cd_pipelines):
                cd_name = cd_pipeline.get('name', f'cd-pipeline-{cd_idx + 1}')
                
                cd_task_names = set()
                cd_duplicate_tasks = set()
                
                # Collect pre_cd_configs task names
                pre_cd_tasks = cd_pipeline.get('pre_cd_configs', {}).get('tasks', [])
                for task in pre_cd_tasks:
                    task_name = task.get('task_name')
                    if task_name:
                        if task_name in cd_task_names:
                            cd_duplicate_tasks.add(task_name)
                        else:
                            cd_task_names.add(task_name)
                
                # Collect post_cd_configs task names
                post_cd_tasks = cd_pipeline.get('post_cd_configs', {}).get('tasks', [])
                for task in post_cd_tasks:
                    task_name = task.get('task_name')
                    if task_name:
                        if task_name in cd_task_names:
                            cd_duplicate_tasks.add(task_name)
                        else:
                            cd_task_names.add(task_name)
                
                if cd_duplicate_tasks:
                    return {
                        'success': False,
                        'error': f'Duplicate task_name(s) found in CD pipeline "{cd_name}": {", ".join(sorted(cd_duplicate_tasks))}. Task names must be unique across pre_cd_configs and post_cd_configs.'
                    }
        
        return None

    def __init__(self, base_url, api_token):
        """
        Initialize the Devtron API client.
        
        Args:
            base_url (str): The base URL of the Devtron instance
            api_token (str): The API token for authentication
        """
        self.base_url  = base_url.rstrip('/')
        self.api_token = api_token
        self.headers   = {
            'token': api_token,
            'Content-Type': 'application/json'
        }
        # Initialize handler/helper objects with required arguments
        self.base_config         = BaseConfiguration(self.base_url,  self.headers)
        self.build_config        = BuildConfig(self.base_url,        self.headers)
        self.git_handler         = GitHandler(self.base_url,         self.headers)
        self.update_git_handler  = UpdateGitHandler(self.base_url,   self.headers)
        self.utils               = DevtronUtils(self.base_url,       self.headers)
        self.workflow            = Workflow(self.base_url,           self.headers)
        self.metadata            = DevtronAppMetadata(self.base_url, self.headers)
        self.update_build_config = UpdateBuildConfig(self.base_url,  self.headers, self.git_handler)
        self.override_config     = OverrideDeploymentTemplateHandler(self.base_url, self.headers)

        # Validate the Devtron environment
        self._validate_environment()


    def create_application(self, config_data):
        # Validation for duplicate environments and unique pipeline names
        validation_error = self._validate_workflow_env_and_pipeline_names(config_data)
        if validation_error:
            return validation_error
        
        # Validation for unique task names within each pipeline
        task_name_validation_error = self._validate_task_name_uniqueness(config_data)
        if task_name_validation_error:
            return task_name_validation_error
        """
        Create a new application in Devtron.
        
        Args:
            config_data (dict): Configuration data from YAML file
            
        Returns:
            dict: Result of the operation with success status and app ID or error message
        """
        try:
            print("Creating application...")
            
            # Normalize case-sensitive fields in config_data
            config_data = self._normalize_config_data(config_data)
            
            # Extract application details from config
            app_name         = config_data.get('app_name')
            project_name     = config_data.get('project_name')
            description      = config_data.get('description', '')
            labels           = config_data.get('labels', [])
            git_repositories = config_data.get('git_repositories', [])
            
            if not app_name or not project_name:
                return {
                    'success': False,
                    'error': 'app_name and project_name are required in config'
                }
            
            # Validate labels if present
            if labels:
                validation_result = validate_labels(labels)
                if not validation_result['success']:
                    error_message = 'Label validation failed:\n' + '\n'.join(validation_result['errors'])
                    return {
                        'success': False,
                        'error': error_message
                    }
            
            # Get team ID from project name
            print(f"Getting team ID for project: {project_name}")
            team_result = self.utils.get_team_id_by_project_name(project_name)
            if not team_result['success']:
                return {
                    'success': False,
                    'error': f'Could not get team ID for project {project_name}: {team_result["error"]}'
                }
            
            team_id = team_result['team_id']
            print(f"Found team ID: {team_id}")
            
            # Prepare payload for application creation
            payload = {
                'appName': app_name,
                'teamId': team_id,
                'description': description,
                'labels': labels,
                'appType': None
            }
            
            # Make API call to create application
            print(f"Creating application: {app_name}")
            response = requests.post(
                f'{self.base_url}/orchestrator/app',
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # Check response status
            if response.status_code == 200:
                result = response.json()
                # Extract app ID from the result field
                app_id = result.get('result', {}).get('id')
                if app_id:
                    print(f"Application created successfully with ID: {app_id}")

                    # If git repositories are provided, add them to the application
                    if git_repositories:
                        print(f"Adding {len(git_repositories)} git repositories to the application")
                        git_config = {
                            'app_id': app_id,
                            'git_repositories': git_repositories
                        }
                        git_result = self.git_handler.add_git_material(git_config)
                        if not git_result['success']:
                            return {
                                'success': False,
                                'error': f'Application created but failed to add git material: {git_result["error"]}'
                            }
                        print("All git repositories added successfully")
                    
                    # Fetch application details
                    print("Fetching application details...")
                    app_details = self.utils.get_application_details(app_id)
                    if not app_details["success"]:
                        return {
                            "success": False,
                            "error": f"Application created but failed to fetch details: {app_details['error']}"
                        }
                    print("Git details fetched successfully!!! ")
                    
                    material_ids = app_details["material_ids"]
                    if not material_ids:
                        return {
                            "success": False,
                            "error": "No Git Material IDs found to configure CI pipeline."
                        }

                    build_configuration_result = self.build_config.configure_ci_pipeline(app_id, material_ids[0],config_data)
                    if not build_configuration_result["success"]:
                        return {
                            "success": False,
                            "error": f"Application created but failed to configure buildconfig: {build_configuration_result['error']}"
                        }

                    # Setup base configurations if config provided
                    if config_data.get('base_configurations'):
                        print("Setting up base configurations...")
                        base_config_result = self.base_config.setup_base_configurations(app_id, config_data)
                        if not base_config_result['success']:
                            return {
                                'success': False,
                                'error': f"Application created but failed to setup base configurations: {base_config_result['error']}"
                            }
                    workflows = config_data.get('workflows')

                    if workflows:
                        print("Setting up workflows...")
                        workflow_errors = []
                        workflows_created = 0
                        
                        for i, w in enumerate(workflows):
                            ci_pipeline_name = w.get('ci_pipeline', {}).get('name', f'workflow-{i+1}')
                            print(f"Creating workflow with CI pipeline: {ci_pipeline_name}")
                            
                            workflow_creation_result = self.workflow.create_workflow(w, app_id)
                            if not workflow_creation_result or not workflow_creation_result.get('success', False):
                                error_msg = f"Failed to create workflow '{ci_pipeline_name}': {workflow_creation_result.get('error', 'Unknown error')}"
                                print(f"WARNING: {error_msg}")
                                workflow_errors.append(error_msg)
                            else:
                                workflows_created += 1
                                print(f"Successfully created workflow '{ci_pipeline_name}'")
                        
                        if workflow_errors:
                            if workflows_created == 0:
                                return {
                                    'success': False,
                                    'error': f"Application created but failed to create any workflows. Errors: {'; '.join(workflow_errors)}"
                                }
                            else:
                                print(f"WARNING: {workflows_created}/{len(workflows)} workflows created successfully. Errors encountered:")
                                for error in workflow_errors:
                                    print(f"  - {error}")
                        
                        print(f"Workflow creation completed: {workflows_created}/{len(workflows)} workflows created successfully")
                    return {
                        'success': True,
                        'app_id': app_id
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Could not extract app ID from response'
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

    def _normalize_config_data(self, config_data):

        """
        Normalize case-sensitive fields in config data to their expected case.
        
        Args:
            config_data (dict): Configuration data from YAML file
            
        Returns:
            dict: Normalized configuration data
        """
        if not isinstance(config_data, dict):
            return config_data
            
        normalized_data = config_data.copy()
        
        # Normalize build_configurations
        if 'build_configurations' in normalized_data:
            build_config = normalized_data['build_configurations']
            if isinstance(build_config, dict):
                # Normalize build_type
                if 'build_type' in build_config:
                    build_config['build_type'] = self._normalize_build_type(build_config['build_type'])
                
                # Normalize target_platform
                if 'target_platform' in build_config and isinstance(build_config['target_platform'], str):
                    build_config['target_platform'] = build_config['target_platform'].lower()
                
        # Normalize base_configurations
        if 'base_configurations' in normalized_data:
            base_config = normalized_data['base_configurations']
            if isinstance(base_config, dict):
                # Normalize deployment_template
                if 'deployment_template' in base_config:
                    dt_config = base_config['deployment_template']
                    if isinstance(dt_config, dict) and 'chart_type' in dt_config:
                        dt_config['chart_type'] = self._normalize_chart_type(dt_config['chart_type'])
                        
                    # Normalize show_application_metrics
                    if 'show_application_metrics' in dt_config:
                        dt_config['show_application_metrics'] = self._normalize_boolean(dt_config['show_application_metrics'])
                
                # Normalize config_maps and secrets
                for config_type in ['config_maps', 'secrets']:
                    if config_type in base_config:
                        config_items = base_config[config_type]
                        if isinstance(config_items, list):
                            for item in config_items:
                                if isinstance(item, dict):
                                    # Normalize external
                                    if 'external' in item:
                                        item['external'] = self._normalize_boolean(item['external'])
                                    
                                    # Normalize subPath
                                    if 'subPath' in item:
                                        item['subPath'] = self._normalize_boolean_or_string(item['subPath'])
                                    
        # Normalize workflows
        if 'workflows' in normalized_data:
            workflows = normalized_data['workflows']
            if isinstance(workflows, list):
                for workflow in workflows:
                    if isinstance(workflow, dict):
                        # Normalize ci_pipeline
                        if 'ci_pipeline' in workflow:
                            ci_pipeline = workflow['ci_pipeline']
                            if isinstance(ci_pipeline, dict):
                                # Normalize type
                                if 'type' in ci_pipeline:
                                    ci_pipeline['type'] = self._normalize_ci_pipeline_type(ci_pipeline['type'])
                                
                                # Normalize is_manual
                                if 'is_manual' in ci_pipeline:
                                    ci_pipeline['is_manual'] = self._normalize_boolean(ci_pipeline['is_manual'])
                                
                                # Normalize branches
                                if 'branches' in ci_pipeline and isinstance(ci_pipeline['branches'], list):
                                    for branch in ci_pipeline['branches']:
                                        if isinstance(branch, dict) and 'type' in branch:
                                            branch['type'] = self._normalize_branch_type(branch['type'])
                                # Normalize custom tasks in pre/post build configs
                                for build_section in ['pre_build_configs', 'post_build_configs']:
                                    if build_section in ci_pipeline and isinstance(ci_pipeline[build_section], dict):
                                        self._normalize_tasks_section(ci_pipeline[build_section])
                        
                        # Normalize cd_pipelines
                        if 'cd_pipelines' in workflow:
                            cd_pipelines = workflow['cd_pipelines']
                            if isinstance(cd_pipelines, list):
                                for cd_pipeline in cd_pipelines:
                                    if isinstance(cd_pipeline, dict):
                                        # Normalize deployment_type
                                        if 'deployment_type' in cd_pipeline:
                                            cd_pipeline['deployment_type'] = cd_pipeline['deployment_type'].lower()
                                        
                                        # Normalize is_manual
                                        if 'is_manual' in cd_pipeline:
                                            cd_pipeline['is_manual'] = self._normalize_boolean(cd_pipeline['is_manual'])
                                        
                                        # Normalize placement
                                        if 'placement' in cd_pipeline:
                                            cd_pipeline['placement'] = cd_pipeline['placement'].lower()
                                        
                                        # Normalize deployment_strategies
                                        if 'deployment_strategies' in cd_pipeline and isinstance(cd_pipeline['deployment_strategies'], list):
                                            for strategy in cd_pipeline['deployment_strategies']:
                                                if isinstance(strategy, dict) and 'name' in strategy:
                                                    strategy['name'] = self._normalize_strategy_name(strategy['name'])
                                                
                                                # Normalize default flag
                                                if isinstance(strategy, dict) and 'default' in strategy:
                                                    strategy['default'] = self._normalize_boolean(strategy['default'])
                                        
                                        # Normalize env_configuration
                                        if 'env_configuration' in cd_pipeline:
                                            env_config = cd_pipeline['env_configuration']
                                            if isinstance(env_config, dict):
                                                # Normalize deployment_template
                                                if 'deployment_template' in env_config:
                                                    dt_config = env_config['deployment_template']
                                                    if isinstance(dt_config, dict):
                                                        # Normalize merge_strategy
                                                        if 'merge_strategy' in dt_config:
                                                            dt_config['merge_strategy'] = dt_config['merge_strategy'].lower()
                                                        
                                                        # Normalize show_application_metrics
                                                        if 'show_application_metrics' in dt_config:
                                                            dt_config['show_application_metrics'] = self._normalize_boolean(dt_config['show_application_metrics'])
                                                
                                                # Normalize config_maps and secrets
                                                for config_type in ['config_maps', 'secrets']:
                                                    if config_type in env_config:
                                                        config_items = env_config[config_type]
                                                        if isinstance(config_items, list):
                                                            for item in config_items:
                                                                if isinstance(item, dict):
                                                                    # Normalize type
                                                                    if 'type' in item:
                                                                        item['type'] = item['type'].lower()
                                                                    
                                                                    # Normalize external
                                                                    if 'external' in item:
                                                                        item['external'] = self._normalize_boolean(item['external'])
                                                                    
                                                                    # Normalize subPath
                                                                    if 'subPath' in item:
                                                                        item['subPath'] = self._normalize_boolean_or_string(item['subPath'])
                                                                    
                                                                    # Normalize merge_strategy
                                                                    if 'merge_strategy' in item:
                                                                        item['merge_strategy'] = item['merge_strategy'].lower()
                                                # Normalize custom tasks in pre/post cd configs
                                                for cd_section in ['pre_cd_configs', 'post_cd_configs']:
                                                    if cd_section in env_config and isinstance(env_config[cd_section], dict):
                                                        self._normalize_tasks_section(env_config[cd_section])
        
        # Normalize config_approval
        if 'config_approval' in normalized_data:
            config_approval = normalized_data['config_approval']
            if isinstance(config_approval, dict):
                # Normalize action
                if 'action' in config_approval:
                    config_approval['action'] = config_approval['action'].lower()
                
                # Normalize if_draft_already_exists
                if 'if_draft_already_exists' in config_approval:
                    config_approval['if_draft_already_exists'] = config_approval['if_draft_already_exists'].lower()
                
                # Normalize notify_all
                if 'notify_all' in config_approval:
                    config_approval['notify_all'] = self._normalize_boolean(config_approval['notify_all'])
        
        return normalized_data

    def _normalize_build_type(self, build_type):
        """Normalize build_type to expected case."""
        if not isinstance(build_type, str):
            return build_type
            
        build_type_lower = build_type.lower()
        build_type_mapping = {
            'dockerfileexists': 'DockerfileExists',
            'createdockerfile': 'CreateDockerfile',
            'buildpacks': 'Buildpacks'
        }
        return build_type_mapping.get(build_type_lower, build_type)

    def _normalize_chart_type(self, chart_type):
        """Normalize chart_type to expected case."""
        if not isinstance(chart_type, str):
            return chart_type
            
        chart_type_lower = chart_type.lower()
        chart_type_mapping = {
            'job & cronjob': 'Job & CronJob',
            'deployment': 'Deployment',
            'statefulset': 'StatefulSet',
            'gpu-workload': 'GPU-Workload',
            'rollout deployment': 'Rollout Deployment'
        }
        # Try exact match first
        for key, value in chart_type_mapping.items():
            if key == chart_type_lower:
                return value
        # Try case-insensitive partial match
        for key, value in chart_type_mapping.items():
            if key.lower() == chart_type_lower:
                return value
        return chart_type

    def _normalize_ci_pipeline_type(self, pipeline_type):
        """Normalize CI pipeline type to expected case."""
        if not isinstance(pipeline_type, str):
            return pipeline_type
            
        pipeline_type_lower = pipeline_type.lower()
        pipeline_type_mapping = {
            'ci_job': 'CI_JOB',
            'linked': 'LINKED',
            'linked_cd': 'LINKED_CD',
            'ci_build': 'CI_BUILD'
        }
        return pipeline_type_mapping.get(pipeline_type_lower, pipeline_type)

    def _normalize_branch_type(self, branch_type):
        """Normalize branch type to expected case."""
        if not isinstance(branch_type, str):
            return branch_type
            
        branch_type_lower = branch_type.lower()
        branch_type_mapping = {
            'source_type_branch_fixed': 'SOURCE_TYPE_BRANCH_FIXED',
            'source_type_branch_regex': 'SOURCE_TYPE_BRANCH_REGEX'
        }
        return branch_type_mapping.get(branch_type_lower, branch_type)

    def _normalize_strategy_name(self, strategy_name):
        """Normalize deployment strategy name to expected case."""
        if not isinstance(strategy_name, str):
            return strategy_name
            
        strategy_name_lower = strategy_name.lower()
        strategy_name_mapping = {
            'rolling': 'Rolling',
            'recreate': 'recreate',
            'blue-green': 'BLUE-GREEN',
            'canary': 'CANARY'
        }
        return strategy_name_mapping.get(strategy_name_lower, strategy_name)

    def _normalize_boolean(self, value):
        """Normalize boolean values from various formats."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ['true', '1', 'yes', 'on']:
                return True
            elif value_lower in ['false', '0', 'no', 'off']:
                return False
        elif isinstance(value, (int, float)):
            return bool(value)
        return value

    def _normalize_boolean_or_string(self, value):
        """Normalize values that can be boolean or string."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ['true', '1', 'yes', 'on']:
                return True
            elif value_lower in ['false', '0', 'no', 'off']:
                return False
        return value

    def _validate_environment(self):
        """
        Validates the Devtron environment by checking the server mode and license status.
        Exits if the server is not in 'FULL' mode or if the license is not valid.
        """
        try:
            print("Validating Devtron environment...")
            version_url = f'{self.base_url}/orchestrator/version'
            response = requests.get(version_url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    result = data.get('result', {})
                    server_mode = result.get('serverMode')
                    license_status = response.headers.get('x-license-status')

                    if server_mode != "FULL":
                        error_message = f"Devtron server must be in 'FULL' mode. Current mode: {server_mode}"
                        print(f"Error: {error_message}")
                        raise ValueError(error_message)
                    
                    if license_status != 'valid':
                        error_message = f"Devtron license status is not valid or expired. Please check your license."
                        print(f"Error: {error_message}")
                        raise ValueError(error_message)
                    
                    print("Devtron environment validation successful.")
                else:
                    error_message = f"Failed to get Devtron version information. API Code: {data.get('code')}"
                    print(f"Error: {error_message}")
                    raise ValueError(error_message)
            elif response.status_code == 401:
                error_message = "Failed to connect to Devtron API. The token has either expired or is invalid. Please check your API token."
                raise ConnectionError(error_message)
            else:
                error_message = f"Failed to connect to Devtron API. Status code: {response.status_code}"
                raise ConnectionError(error_message)
        except requests.exceptions.RequestException as e:
            error_message = f"Could not connect to Devtron server at {self.base_url}. {e}"
            raise ConnectionError(error_message)
        except ValueError as e:
            # Re-raise ValueError to be handled by the caller
            raise e
        except ConnectionError as e:
            # Re-raise ConnectionError to be handled by the caller
            raise e
        except Exception as e:
            error_message = f"An unexpected error occurred during environment validation: {e}"
            raise RuntimeError(error_message)

    def _extract_ci_branches(self, ci_pipeline_details):
        """
        Extract branch information from CI pipeline details.
        
        Args:
            ci_pipeline_details (dict): CI pipeline details from API
            
        Returns:
            list: List of branch configurations
        """
        branches = []
        ci_material = ci_pipeline_details.get('ciMaterial', [])
        
        for material in ci_material:
            source = material.get('source', {})
            if source:
                branch_config = {
                    'type': source.get('type'),
                    'branch': source.get('value'),
                    'regex': source.get('regex')
                }
                # Remove None values
                branch_config = {k: v for k, v in branch_config.items() if v is not None}
                if branch_config:
                    branches.append(branch_config)
        
        return branches
    
    def _format_script_for_yaml(self, script_content):
        """
        Formats a script string to be represented as a multi-line block in YAML.
        Converts escaped newlines to actual newlines and ensures the string ends with a newline.
        """
        if isinstance(script_content, str):
            # Convert escaped newlines to actual newlines
            script_content = script_content.replace('\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
            # Ensure the script ends with a newline for proper YAML formatting
            if script_content and not script_content.endswith('\n'):
                script_content += '\n'
            return script_content
        return script_content
    
    def delete_application(self, app_name, approve=False):
        """
        Delete an application and all its associated pipelines following the correct deletion order.
        
        Args:
            app_name (str): Name of the application to delete
            approve (bool): Whether to proceed with deletion (safety mechanism)
            
        Returns:
            dict: Result of the operation with success status or error message
        """
        try:
            if not approve:
                return {
                    'success': False,
                    'error': 'Deletion requires explicit approval. Please add --approve flag to confirm deletion.'
                }
            
            print(f"Starting deletion process for application: {app_name}")
            
            # Get application ID by name
            app_id_result = self.utils.get_application_id_by_name(app_name)
            if not app_id_result['success']:
                return {
                    'success': False,
                    'error': f'Could not find application {app_name}: {app_id_result["error"]}'
                }
            
            app_id = app_id_result['app_id']
            print(f"Found application ID: {app_id}")
            
            # Get all CI pipelines for the application
            ci_pipelines_result = self.utils.get_ci_pipelines(app_id)
            if not ci_pipelines_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to fetch CI pipelines: {ci_pipelines_result["error"]}'
                }
            
            ci_pipelines = ci_pipelines_result['ci_pipelines']
            print(f"Found {len(ci_pipelines)} CI pipelines")
            
            # Create a map of CI pipeline ID to CI pipeline details for easy lookup
            ci_pipeline_map = {pipeline['id']: pipeline for pipeline in ci_pipelines}
            
            # Get all workflows for the application to find CD pipelines and their relationships
            workflows_result = self.utils.get_workflows(app_id)
            if not workflows_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to fetch workflows: {workflows_result["error"]}'
                }
            
            workflows = workflows_result['workflows']
            print(f"Found {len(workflows)} workflows to process")
            
            # Process workflows and categorize pipelines according to deletion order
            linked_cd_pipelines = []  # CD pipelines attached to LINKED_CD CI pipelines
            linked_cd_ci_pipelines = []  # LINKED_CD CI pipelines
            linked_pipelines = []  # CD pipelines attached to LINKED CI pipelines
            linked_ci_pipelines = []  # LINKED CI pipelines
            webhook_cd_pipelines = []  # CD pipelines attached to WEBHOOK
            ci_job_pipelines = []  # CI_JOB CI pipelines
            ci_build_pipelines = []  # CI_BUILD CI pipelines
            cd_pipeline_details = []  # All CD pipeline details for ordering
            
            # Keep track of all CI pipelines we've already categorized to avoid duplicates
            categorized_ci_pipelines = set()
            
            # Process workflows to categorize pipelines
            for workflow in workflows:
                workflow_id = workflow['id']
                workflow_name = workflow['name']
                print(f"Processing workflow: {workflow_name} (ID: {workflow_id})")
                
                # Process tree nodes
                tree = workflow.get('tree', [])
                
                # First pass: Identify CI pipeline types
                ci_pipeline_types = {}
                for node in tree:
                    if node.get('type') == 'CI_PIPELINE':
                        ci_pipeline_id = node.get('componentId')
                        # Find the CI pipeline in our map to get its type
                        ci_pipeline = ci_pipeline_map.get(ci_pipeline_id)
                        if ci_pipeline:
                            pipeline_type = ci_pipeline.get('pipelineType', '')
                            ci_pipeline_types[ci_pipeline_id] = {
                                'type': pipeline_type,
                                'name': ci_pipeline.get('name', ''),
                                'workflow_id': workflow_id
                            }
                
                # Second pass: Categorize CD pipelines based on their parent types
                for node in tree:
                    if node.get('type') == 'CD_PIPELINE':
                        parent_type = node.get('parentType', '')
                        parent_id = node.get('parentId', 0)
                        cd_pipeline_id = node.get('componentId')
                        is_last = node.get('isLast', False)
                        
                        cd_detail = {
                            'id': cd_pipeline_id,
                            'parent_type': parent_type,
                            'parent_id': parent_id,
                            'is_last': is_last,
                            'workflow_id': workflow_id
                        }
                        cd_pipeline_details.append(cd_detail)
                        
                        # Check if this CD pipeline is attached to a LINKED_CD CI pipeline
                        if parent_type == 'CI_PIPELINE' and parent_id in ci_pipeline_types:
                            parent_ci = ci_pipeline_types[parent_id]
                            if parent_ci['type'] == 'LINKED_CD':
                                linked_cd_pipelines.append(cd_detail)
                                # Also track the CI pipeline for later deletion
                                if parent_id not in [p['id'] for p in linked_cd_ci_pipelines]:
                                    linked_cd_ci_pipelines.append({
                                        'id': parent_id,
                                        'name': parent_ci['name'],
                                        'workflow_id': parent_ci['workflow_id']
                                    })
                                    categorized_ci_pipelines.add(parent_id)
                            elif parent_ci['type'] == 'LINKED':
                                linked_pipelines.append(cd_detail)
                                # Also track the CI pipeline for later deletion
                                if parent_id not in [p['id'] for p in linked_ci_pipelines]:
                                    linked_ci_pipelines.append({
                                        'id': parent_id,
                                        'name': parent_ci['name'],
                                        'workflow_id': parent_ci['workflow_id']
                                    })
                                    categorized_ci_pipelines.add(parent_id)
                        
                        # Check for WEBHOOK parent type
                        elif parent_type == 'WEBHOOK':
                            webhook_cd_pipelines.append(cd_detail)
                        
                        # Other CD pipelines will be handled in the general deletion order
                
                # Categorize remaining CI pipelines (those not already categorized)
                for ci_pipeline_id, ci_info in ci_pipeline_types.items():
                    # Skip CI pipelines we've already identified for special handling
                    if ci_pipeline_id in categorized_ci_pipelines:
                        continue
                    
                    # Mark this CI pipeline as categorized
                    categorized_ci_pipelines.add(ci_pipeline_id)
                    
                    # Handle any CI pipelines not attached to CD pipelines (orphans)
                    if ci_info['type'] == 'CI_JOB':
                        ci_job_pipelines.append({
                            'id': ci_pipeline_id,
                            'name': ci_info['name'],
                            'workflow_id': ci_info['workflow_id']
                        })
                    elif ci_info['type'] == 'CI_BUILD':
                        ci_build_pipelines.append({
                            'id': ci_pipeline_id,
                            'name': ci_info['name'],
                            'workflow_id': ci_info['workflow_id']
                        })
                    elif ci_info['type'] == 'LINKED_CD':
                        linked_cd_ci_pipelines.append({
                            'id': ci_pipeline_id,
                            'name': ci_info['name'],
                            'workflow_id': ci_info['workflow_id']
                        })
                    elif ci_info['type'] == 'LINKED':
                        linked_ci_pipelines.append({
                            'id': ci_pipeline_id,
                            'name': ci_info['name'],
                            'workflow_id': ci_info['workflow_id']
                        })
            
            # Now perform deletions in the correct order:
            # 1. Delete CD pipelines attached to LINKED_CD CI pipelines first
            print(f"Deleting {len(linked_cd_pipelines)} CD pipelines attached to LINKED_CD CI pipelines...")
            for cd_pipeline in linked_cd_pipelines:
                delete_result = self.workflow.delete_cd_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    cd_pipeline_id=cd_pipeline['id']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CD pipeline {cd_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
            
            # 2. Delete LINKED_CD CI pipelines
            print(f"Deleting {len(linked_cd_ci_pipelines)} LINKED_CD CI pipelines...")
            for ci_pipeline in linked_cd_ci_pipelines:
                delete_result = self.workflow.delete_ci_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    app_workflow_id=ci_pipeline['workflow_id'],
                    ci_pipeline_id=ci_pipeline['id'],
                    ci_pipeline_name=ci_pipeline['name']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CI pipeline {ci_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CI pipeline: {ci_pipeline['id']} (Name: {ci_pipeline['name']})")
            
            # 3. Delete CD pipelines attached to LINKED CI pipelines
            print(f"Deleting {len(linked_pipelines)} CD pipelines attached to LINKED CI pipelines...")
            for cd_pipeline in linked_pipelines:
                delete_result = self.workflow.delete_cd_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    cd_pipeline_id=cd_pipeline['id']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CD pipeline {cd_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
            
            # 4. Delete LINKED CI pipelines
            print(f"Deleting {len(linked_ci_pipelines)} LINKED CI pipelines...")
            for ci_pipeline in linked_ci_pipelines:
                delete_result = self.workflow.delete_ci_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    app_workflow_id=ci_pipeline['workflow_id'],
                    ci_pipeline_id=ci_pipeline['id'],
                    ci_pipeline_name=ci_pipeline['name']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CI pipeline {ci_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CI pipeline: {ci_pipeline['id']} (Name: {ci_pipeline['name']})")
            
            # 5. Delete CD pipelines attached to WEBHOOK (in order: is_last true + parentType webhook, then parentType webhook)
            print(f"Deleting {len(webhook_cd_pipelines)} CD pipelines attached to WEBHOOK...")
            # Sort webhook CD pipelines: is_last=True first
            webhook_cd_pipelines.sort(key=lambda x: not x['is_last'])
            for cd_pipeline in webhook_cd_pipelines:
                delete_result = self.workflow.delete_cd_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    cd_pipeline_id=cd_pipeline['id']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CD pipeline {cd_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
            
            # 6. Delete remaining CD pipelines in the specified order with dependency handling
            print("Deleting remaining CD pipelines...")
            # Get remaining CD pipelines that haven't been deleted yet
            all_cd_pipeline_ids = [cd_detail['id'] for cd_detail in cd_pipeline_details]
            already_deleted_cd_ids = (
                [p['id'] for p in linked_cd_pipelines] +
                [p['id'] for p in linked_pipelines] +
                [p['id'] for p in webhook_cd_pipelines]
            )
            remaining_cd_pipeline_ids = [cd_id for cd_id in all_cd_pipeline_ids if cd_id not in already_deleted_cd_ids]
            
            # Keep trying to delete CD pipelines in the correct order until all are deleted or no progress is made
            max_iterations = 10
            iteration = 0
            while remaining_cd_pipeline_ids and iteration < max_iterations:
                iteration += 1
                print(f"  Iteration {iteration} - Processing {len(remaining_cd_pipeline_ids)} remaining CD pipelines...")
                
                # Refresh workflow data to get current state after previous deletions
                workflows_result = self.utils.get_workflows(app_id)
                if not workflows_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to refresh workflows: {workflows_result["error"]}'
                    }
                
                workflows = workflows_result['workflows']
                
                # Rebuild CD pipeline details with current workflow data
                current_cd_pipeline_details = []
                for workflow in workflows:
                    tree = workflow.get('tree', [])
                    for node in tree:
                        if node.get('type') == 'CD_PIPELINE':
                            cd_detail = {
                                'id': node.get('componentId'),
                                'parent_type': node.get('parentType', ''),
                                'parent_id': node.get('parentId', 0),
                                'is_last': node.get('isLast', False),
                                'workflow_id': workflow['id']
                            }
                            # Only include pipelines that are still remaining to be deleted
                            if cd_detail['id'] in remaining_cd_pipeline_ids:
                                current_cd_pipeline_details.append(cd_detail)
                
                # Categorize CD pipelines based on current state
                cd_pipelines_is_last_cd_parent = []
                cd_pipelines_cd_parent = []
                cd_pipelines_is_last_ci_parent = []
                
                for cd_detail in current_cd_pipeline_details:
                    if cd_detail['id'] in already_deleted_cd_ids:
                        continue
                    
                    if cd_detail['is_last'] and cd_detail['parent_type'] == 'CD_PIPELINE':
                        cd_pipelines_is_last_cd_parent.append(cd_detail)
                    elif cd_detail['parent_type'] == 'CD_PIPELINE':
                        cd_pipelines_cd_parent.append(cd_detail)
                    elif cd_detail['is_last'] and cd_detail['parent_type'] == 'CI_PIPELINE':
                        cd_pipelines_is_last_ci_parent.append(cd_detail)
                
                # Track progress in this iteration
                deleted_in_this_iteration = 0
                
                # Delete in order
                for cd_pipeline in cd_pipelines_is_last_cd_parent:
                    if cd_pipeline['id'] in already_deleted_cd_ids:
                        continue
                    delete_result = self.workflow.delete_cd_pipeline(
                        base_url=self.base_url,
                        headers=self.headers,
                        app_id=app_id,
                        cd_pipeline_id=cd_pipeline['id']
                    )
                    if delete_result['success']:
                        print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
                        already_deleted_cd_ids.append(cd_pipeline['id'])
                        deleted_in_this_iteration += 1
                    else:
                        # Extract userMessage from error if it's a JSON response with userMessage
                        error_message = delete_result['error']
                        try:
                            error_data = json.loads(error_message)
                            if isinstance(error_data, dict) and 'errors' in error_data and error_data['errors']:
                                first_error = error_data['errors'][0]
                                if 'userMessage' in first_error:
                                    error_message = first_error['userMessage']
                                elif 'internalMessage' in first_error:
                                    error_message = first_error['internalMessage']
                        except (json.JSONDecodeError, TypeError, KeyError):
                            # If we can't parse or extract userMessage, keep the original error
                            pass
                        
                        print(f"  Failed to delete CD pipeline {cd_pipeline['id']}: {error_message}")
                
                for cd_pipeline in cd_pipelines_cd_parent:
                    if cd_pipeline['id'] in already_deleted_cd_ids:
                        continue
                    delete_result = self.workflow.delete_cd_pipeline(
                        base_url=self.base_url,
                        headers=self.headers,
                        app_id=app_id,
                        cd_pipeline_id=cd_pipeline['id']
                    )
                    if delete_result['success']:
                        print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
                        already_deleted_cd_ids.append(cd_pipeline['id'])
                        deleted_in_this_iteration += 1
                    else:
                        print(f"  Failed to delete CD pipeline {cd_pipeline['id']}: {delete_result['error']}")
                
                for cd_pipeline in cd_pipelines_is_last_ci_parent:
                    if cd_pipeline['id'] in already_deleted_cd_ids:
                        continue
                    delete_result = self.workflow.delete_cd_pipeline(
                        base_url=self.base_url,
                        headers=self.headers,
                        app_id=app_id,
                        cd_pipeline_id=cd_pipeline['id']
                    )
                    if delete_result['success']:
                        print(f"  Deleted CD pipeline: {cd_pipeline['id']}")
                        already_deleted_cd_ids.append(cd_pipeline['id'])
                        deleted_in_this_iteration += 1
                    else:
                        print(f"  Failed to delete CD pipeline {cd_pipeline['id']}: {delete_result['error']}")
                
                # Update remaining CD pipeline IDs
                remaining_cd_pipeline_ids = [cd_id for cd_id in all_cd_pipeline_ids if cd_id not in already_deleted_cd_ids]
                
                # If no progress was made in this iteration, break to avoid infinite loop
                if deleted_in_this_iteration == 0:
                    print(f"  No progress made in iteration {iteration}, stopping CD pipeline deletion")
                    break
            
            # Check if all CD pipelines were deleted
            if remaining_cd_pipeline_ids:
                return {
                    'success': False,
                    'error': f'Failed to delete CD pipelines {remaining_cd_pipeline_ids} after {iteration} iterations. They may have unresolvable dependencies.'
                }
            
            # 7. Delete CI_JOB CI pipelines
            print(f"Deleting {len(ci_job_pipelines)} CI_JOB CI pipelines...")
            for ci_pipeline in ci_job_pipelines:
                delete_result = self.workflow.delete_ci_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    app_workflow_id=ci_pipeline['workflow_id'],
                    ci_pipeline_id=ci_pipeline['id'],
                    ci_pipeline_name=ci_pipeline['name']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CI pipeline {ci_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CI pipeline: {ci_pipeline['id']} (Name: {ci_pipeline['name']})")
            
            # 8. Delete CI_BUILD CI pipelines
            print(f"Deleting {len(ci_build_pipelines)} CI_BUILD CI pipelines...")
            for ci_pipeline in ci_build_pipelines:
                delete_result = self.workflow.delete_ci_pipeline(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    app_workflow_id=ci_pipeline['workflow_id'],
                    ci_pipeline_id=ci_pipeline['id'],
                    ci_pipeline_name=ci_pipeline['name']
                )
                if not delete_result['success']:
                    return {
                        'success': False,
                        'error': f'Failed to delete CI pipeline {ci_pipeline["id"]}: {delete_result["error"]}'
                    }
                print(f"  Deleted CI pipeline: {ci_pipeline['id']} (Name: {ci_pipeline['name']})")
            
            # 9. Delete empty workflows
            print(f"Deleting {len(workflows)} workflows...")
            for workflow in workflows:
                workflow_id = workflow['id']
                delete_result = self.workflow.delete_workflow(
                    base_url=self.base_url,
                    headers=self.headers,
                    app_id=app_id,
                    workflow_id=workflow_id
                )
                # Workflow deletion might fail if workflow is not empty, which is expected
                # We still try to delete all workflows
                if delete_result['success']:
                    print(f"  Deleted workflow: {workflow_id}")
                else:
                    print(f"  Failed to delete workflow {workflow_id} (might not be empty): {delete_result['error']}")
            
            # Now delete the application itself
            print(f"Deleting application: {app_name} (ID: {app_id})")
            response = requests.delete(
                f'{self.base_url}/orchestrator/app/{app_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                print(f"Application {app_name} deleted successfully!")
                return {
                    'success': True,
                    'message': f'Application {app_name} and all associated pipelines deleted successfully!'
                }
            else:
                try:
                    error_result = response.json()
                    error_message = error_result.get('errors', [{}])[0].get('userMessage', '')
                    if error_message:
                        return {
                            'success': False,
                            'error': f'Failed to delete application: {error_message}'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Failed to delete application with status {response.status_code}: {response.text}'
                        }
                except:
                    return {
                        'success': False,
                        'error': f'Failed to delete application with status {response.status_code}: {response.text}'
                    }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }
    
    def update_application(self, config_data, allow_deletion: bool = False):
        # Validation for duplicate environments and unique pipeline names
        validation_error = self._validate_workflow_env_and_pipeline_names(config_data)
        if validation_error:
            return validation_error
        
        # Validation for unique task names within each pipeline
        task_name_validation_error = self._validate_task_name_uniqueness(config_data)
        if task_name_validation_error:
            return task_name_validation_error
        """
        Update an existing application's git materials and container registry in Devtron.
        Args:
            config_data (dict): Configuration data from YAML file
            allow_deletion (bool): Allow deletion of CI pipelines
        Returns:
            dict: Result of the operation with success status and message or error
        """
        try:
            print("Updating application...")
            
            # Normalize case-sensitive fields in config_data
            config_data = self._normalize_config_data(config_data)
            
            # Extract labels for validation
            labels = config_data.get('labels', [])
            
            # Validate labels if present
            if labels:
                validation_result = validate_labels(labels)
                if not validation_result['success']:
                    error_message = 'Label validation failed:\n' + '\n'.join(validation_result['errors'])
                    return {
                        'success': False,
                        'error': error_message
                    }
            
            metadata_save_result = self.metadata.save_metadata(config_data)
            if not metadata_save_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to save metadata: {metadata_save_result["error"]}'
                }

            print("Updating application git materials...")
            git_result = self.update_git_handler.update_git_materials(config_data)
            if not git_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to update git materials: {git_result["error"]}'
                }
            registry_result = self.update_build_config.update_container_registry(config_data)
            if not registry_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to update container registry: {registry_result["error"]}'
                }
            update_base_configurations_result = self.base_config.update_base_configurations(config_data, allow_deletion)
            if not update_base_configurations_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to update base configurations: {update_base_configurations_result["error"]}'
                }
            print("Updating application workflows...")
            update_workflows_result = self.workflow.update_workflows(config_data, allow_deletion)
            if not update_workflows_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to update workflows: {update_workflows_result["error"]}'
                }
            return {
                'success': True,
                'message': 'Application updated: git materials and container registry and base configurations.'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }

    def get_application(self, app_name):
        """
        Get application configuration from Devtron.
        Args:
            app_name (str): Name of the application to fetch
        Returns:
            dict: Application configuration in the same format as used for create-app
        """
        try:
            print(f"Fetching application: {app_name}")
            
            # Get application ID by name
            app_id_result = self.utils.get_application_id_by_name(app_name)
            if not app_id_result['success']:
                return {
                    'success': False,
                    'error': f'Could not find application {app_name}: {app_id_result["error"]}'
                }
            
            app_id = app_id_result['app_id']
            print(f"Found application ID: {app_id}")
            
            # Fetch application details
            app_details_result = self.utils.get_application_details(app_id)
            if not app_details_result['success']:
                return {
                    'success': False,
                    'error': f'Failed to fetch application details: {app_details_result["error"]}'
                }
            
            app_data = app_details_result['data']
            
            # Build configuration data structure
            config_data = {
                'app_name': app_name
            }
            
            # Add description using app metadata endpoint if available
            description = self.utils.get_app_description_from_metadata(app_id)
            if description:
                config_data['description'] = description
            
            # Add labels if available
            if 'labels' in app_data and app_data['labels']:
                config_data['labels'] = app_data['labels']
            
            # Add git repositories if available
            if 'material' in app_data and app_data['material']:
                git_repositories = []
                for material in app_data['material']:
                    git_repo = {
                        'url': material.get('url'),
                        'git_account_name': self.git_handler.get_git_account_name_by_id(app_id, material.get('gitProviderId'))['git_account_name'] if material.get('gitProviderId') is not None else '',
                        'checkout_path': material.get('checkoutPath', './')
                    }
                    
                    # Add optional fields if they exist
                    if 'fetchSubmodules' in material:
                        git_repo['fetch_submodules'] = material['fetchSubmodules']
                    if 'filterPattern' in material and material['filterPattern']:
                        git_repo['filter_pattern'] = material['filterPattern']
                        
                    git_repositories.append(git_repo)
                
                config_data['git_repositories'] = git_repositories
            
            # Fetch CI pipeline configuration
            try:
                pipeline_response = requests.get(
                    f'{self.base_url}/orchestrator/app/ci-pipeline/{app_id}',
                    headers=self.headers
                )
                
                if pipeline_response.status_code == 200:
                    pipeline_data = pipeline_response.json().get('result', {})
                    
                    # Add build configurations if available
                    build_config = {}
                    ci_build_config = pipeline_data.get('ciBuildConfig', {})
                    
                    if 'dockerRegistry' in pipeline_data:
                        build_config['container_registry_name'] = pipeline_data['dockerRegistry']
                    if 'dockerRepository' in pipeline_data:
                        build_config['repository_name'] = pipeline_data['dockerRepository']
                        
                    # Add build type specific configurations
                    # Map Devtron API build types to configuration file build types
                    build_type_mapping = {
                        'self-dockerfile-build': 'DockerfileExists',
                        'managed-dockerfile-build': 'CreateDockerfile',
                        'buildpack-build': 'Buildpacks'
                    }
                    
                    build_type = ci_build_config.get('ciBuildType')
                    if build_type:
                        # Map to the configuration file build type
                        config_build_type = build_type_mapping.get(build_type, build_type)
                        build_config['build_type'] = config_build_type
                        
                        if build_type == 'self-dockerfile-build':
                            docker_config = ci_build_config.get('dockerBuildConfig', {})
                            if 'dockerfileRelativePath' in docker_config:
                                build_config['dockerfile_path'] = docker_config['dockerfileRelativePath']
                            if 'targetPlatform' in docker_config:
                                build_config['target_platform'] = docker_config['targetPlatform']
                            if 'buildContext' in docker_config:
                                build_config['build_context'] = docker_config['buildContext']
                            if 'dockerfileRepository' in docker_config:
                                build_config['dockerfile_repository'] = docker_config['dockerfileRepository']
                            if 'args' in docker_config and docker_config['args']:
                                # Convert args to docker_build_args format
                                build_config['docker_build_args'] = docker_config['args']
                                
                        elif build_type == 'managed-dockerfile-build':
                            docker_config = ci_build_config.get('dockerBuildConfig', {})
                            if 'dockerfileRelativePath' in docker_config:
                                build_config['dockerfile_path'] = docker_config['dockerfileRelativePath']
                            if 'targetPlatform' in docker_config:
                                build_config['target_platform'] = docker_config['targetPlatform']
                            if 'language' in docker_config:
                                build_config['language'] = docker_config['language']
                            if 'languageFramework' in docker_config:
                                build_config['language_framework'] = docker_config['languageFramework']
                            if 'dockerfileContent' in docker_config:
                                build_config['dockerfile_content'] = docker_config['dockerfileContent']
                                
                        elif build_type == 'buildpack-build':
                            buildpack_config = ci_build_config.get('buildPackConfig', {})
                            if 'builderId' in buildpack_config:
                                build_config['builder_image'] = buildpack_config['builderId']
                            if 'language' in buildpack_config:
                                build_config['language'] = buildpack_config['language']
                            if 'languageVersion' in buildpack_config:
                                build_config['version'] = buildpack_config['languageVersion']
                            if 'projectPath' in buildpack_config:
                                build_config['build_context'] = buildpack_config['projectPath']
                    
                    if build_config:
                        config_data['build_configurations'] = build_config
                        
            except Exception as e:
                print(f"Warning: Could not fetch CI pipeline configuration: {str(e)}")
            
            # Fetch base configurations if they exist
            base_configurations = {}
            
            # Fetch deployment template
            try:
                # Get latest chart reference ID
                latest_chart_ref_id = self.base_config.bdt.get_latest_chart_ref_id(app_id)
                if latest_chart_ref_id:
                    deployment_template_result = self.base_config.bdt.get_deployment_template_yaml(app_id, latest_chart_ref_id)
                    if deployment_template_result['success']:
                        deployment_template = deployment_template_result['yaml'].get('globalConfig', {})
                        if deployment_template:
                            # If chart name is not available in deployment template, get it from chart reference API
                            chart_name = self.utils._get_chart_details_from_id(app_id, latest_chart_ref_id).get('name')
                            
                            base_configurations['deployment_template'] = {
                                'version': deployment_template.get('refChartTemplateVersion'),
                                'chart_type': chart_name,
                                'show_application_metrics': deployment_template.get('isAppMetricsEnabled', False)
                            }
                            
                            # Save defaultAppOverride to a file instead of including it directly
                            default_app_override = deployment_template.get('defaultAppOverride', {})
                            if default_app_override:
                                # Create filename based on app name
                                values_filename = f"base-{app_name}-values.yaml"
                                
                                # Write the values to the file
                                with open(values_filename, 'w') as f:
                                    dump_yaml(default_app_override, stream=f)
                                
                                # Reference the file instead of including the values directly
                                base_configurations['deployment_template']['values_path'] = values_filename
            except Exception as e:
                print(f"Warning: Could not fetch deployment template: {str(e)}")
            
            # Fetch config maps and secrets
            try:
                cm_cs_result = self.base_config.devtron_config_map_secret.get_base_cm_cs_details(app_id)
                if cm_cs_result['success']:
                    cm_cs_data = cm_cs_result['result']
                    
                    # Fetch detailed config map data
                    config_maps = []
                    if cm_cs_data.get('cm_list'):
                        for cm_name in cm_cs_data['cm_list']:
                            cm_details_result = self.base_config.devtron_config_map_secret.get_config_map_details(app_id, cm_name)
                            if cm_details_result['success']:
                                # Remove global and overriden fields from config map
                                config_map_data = cm_details_result['config_map']
                                config_map_data.pop('global', None)
                                config_map_data.pop('overridden', None)
                                
                                # Remove subPath field if type is environment
                                if config_map_data.get('type') == 'environment':
                                    config_map_data.pop('subPath', None)
                                    
                                # Handle reverse logic for external config maps with mountPath and subPath
                                # Extract subPath from data object if special conditions are met
                                if (config_map_data.get('external') is True and 
                                    config_map_data.get('mountPath') and 
                                    config_map_data.get('data')):
                                    
                                    # Check if any key in data has an empty string value (indicating it was a subPath)
                                    sub_path_key = None
                                    for key, value in config_map_data['data'].items():
                                        if value == "":
                                            sub_path_key = key
                                            break
                                    
                                    if sub_path_key:
                                        # Set the subPath field and remove the empty entry from data
                                        config_map_data['subPath'] = sub_path_key
                                        del config_map_data['data'][sub_path_key]
                                        
                                        # If data becomes empty after removal, remove the data field entirely
                                        if not config_map_data['data']:
                                            config_map_data.pop('data', None)
                                    
                                # For base configurations, save config map data to a file
                                config_map_values = config_map_data.get('data', {})
                                if config_map_values:
                                    # Create filename based on app name and config map name
                                    cm_filename = f"base-cm-{cm_name}-{app_name}-values.yaml"
                                    
                                    # Write the values to the file
                                    with open(cm_filename, 'w') as f:
                                        dump_yaml(config_map_values, stream=f)
                                    
                                    # Reference the file instead of including the values directly
                                    config_map_data['from_file'] = cm_filename
                                    config_map_data.pop('data', None)
                                    
                                config_maps.append(config_map_data)
                            else:
                                print(f"Warning: Could not fetch details for config map {cm_name}: {cm_details_result['error']}")
                                config_maps.append({'name': cm_name})
                    
                    # Fetch detailed secret data  
                    secrets = []
                    if cm_cs_data.get('cs_list'):
                        for cs_name in cm_cs_data['cs_list']:
                            secret_details_result = self.base_config.devtron_config_map_secret.get_secret_details(app_id, cs_name)
                            if secret_details_result['success']:
                                # Remove global and overriden fields from secret
                                secret_data = secret_details_result['secret']
                                secret_data.pop('global', None)
                                secret_data.pop('overridden', None)
                                
                                # Remove subPath field if type is environment
                                if secret_data.get('type') == 'environment':
                                    secret_data.pop('subPath', None)
                                
                                # Handle reverse logic for external secrets with mountPath and subPath
                                # Extract subPath from data object if special conditions are met
                                if (secret_data.get('external') is True and 
                                    secret_data.get('mountPath') and 
                                    secret_data.get('data')):
                                    
                                    # Check if any key in data has an empty string value (indicating it was a subPath)
                                    sub_path_key = None
                                    for key, value in secret_data['data'].items():
                                        if value == "":
                                            sub_path_key = key
                                            break
                                    
                                    if sub_path_key:
                                        # Set the subPath field and remove the empty entry from data
                                        secret_data['subPath'] = sub_path_key
                                        del secret_data['data'][sub_path_key]
                                        
                                        # If data becomes empty after removal, remove the data field entirely
                                        if not secret_data['data']:
                                            secret_data.pop('data', None)
                                
                                # Base64 decode secret data if present
                                if 'data' in secret_data and secret_data['data']:
                                    decoded_data = {}
                                    for key, encoded_value in secret_data['data'].items():
                                        try:
                                            import base64
                                            decoded_value = base64.b64decode(encoded_value).decode('utf-8')
                                            decoded_data[key] = decoded_value
                                        except Exception as e:
                                            print(f"Warning: Failed to decode base64 value for key '{key}': {e}")
                                            decoded_data[key] = encoded_value  # Keep original if decoding fails
                                    secret_data['data'] = decoded_data
                                    
                                    # For base configurations, save secret data to a file
                                    secret_values = secret_data['data']
                                    if secret_values:
                                        # Create filename based on app name and secret name
                                        secret_filename = f"base-secret-{cs_name}-{app_name}-values.yaml"
                                        
                                        # Write the values to the file
                                        with open(secret_filename, 'w') as f:
                                            dump_yaml(secret_values, stream=f)
                                        
                                        # Reference the file instead of including the values directly
                                        secret_data['from_file'] = secret_filename
                                        secret_data.pop('data', None)
                                    
                                secrets.append(secret_data)
                            else:
                                print(f"Warning: Could not fetch details for secret {cs_name}: {secret_details_result['error']}")
                                secrets.append({'name': cs_name})
                    
                    if config_maps:
                        base_configurations['config_maps'] = config_maps
                    if secrets:
                        base_configurations['secrets'] = secrets
            except Exception as e:
                print(f"Warning: Could not fetch config maps and secrets: {str(e)}")
            
            # Add base configurations to config data if any were found
            if base_configurations:
                config_data['base_configurations'] = base_configurations
            
            # Fetch workflows if they exist
            workflows_data = []
            try:
                workflows_result = self.utils.get_workflows(app_id)
                if workflows_result['success']:
                    workflows = workflows_result['workflows']
                    
                    for workflow in workflows:
                        workflow_info = {}
                        
                        # Process tree nodes to extract pipeline information
                        tree = workflow.get('tree', [])
                        
                        # Find CI pipelines in this workflow
                        for node in tree:
                            if node.get('type') == 'CI_PIPELINE':
                                ci_pipeline_id = node.get('componentId')
                                # Get CI pipeline details
                                ci_pipeline_result = self.utils.get_ci_pipeline_details(app_id, ci_pipeline_id)
                                if ci_pipeline_result['success']:
                                    ci_pipeline_details = ci_pipeline_result['pipeline_details']
                                    
                                    # Extract CI pipeline configuration
                                    ci_pipeline_config = {
                                        'type': ci_pipeline_details.get('pipelineType'),
                                        'is_manual': ci_pipeline_details.get('isManual', False),
                                        'name': ci_pipeline_details.get('name')
                                    }
                                    
                                    # Handle LINKED pipeline source
                                    if ci_pipeline_config['type'] == 'LINKED':
                                        source_app_id = ci_pipeline_details.get('parentAppId')
                                        source_pipeline_id = ci_pipeline_details.get('parentCiPipelineId')
                                        if source_app_id and source_pipeline_id:
                                            # Get source app and pipeline names
                                            source_app_result = self.utils.get_application_details(source_app_id)
                                            if source_app_result['success']:
                                                ci_pipeline_config['source_app'] = source_app_result['data'].get('appName')
                                            
                                            source_pipeline_result = self.utils.get_ci_pipeline_details(source_app_id, source_pipeline_id)
                                            if source_pipeline_result['success']:
                                                ci_pipeline_config['source_pipeline'] = source_pipeline_result['pipeline_details'].get('name')
                                    
                                    # Extract branches information
                                    branches = []
                                    ci_material = ci_pipeline_details.get('ciMaterial', [])
                                    for material in ci_material:
                                        source = material.get('source', {})
                                        if source:
                                            # Use the git material ID as the repo identifier
                                            # This matches the pattern in test.yaml where repo names are simple identifiers
                                            git_material_id = material.get('gitMaterialId')
                                            git_material_name = material.get('gitMaterialName')
                                            repo_identifier = f"{git_material_name}" if git_material_name else "unknown-repo"
                                            
                                            branch_config = {
                                                'repo': repo_identifier,
                                                'branch': source.get('value'),
                                                'type': source.get('type'),
                                                'regex': source.get('regex')
                                            }
                                            # Remove None values
                                            branch_config = {k: v for k, v in branch_config.items() if v is not None}
                                            if branch_config:
                                                branches.append(branch_config)
                                    
                                    if branches:
                                        ci_pipeline_config['branches'] = branches
                                    
                                    # Extract pre-build and post-build configurations
                                    pre_build_stages = ci_pipeline_details.get('preBuildStage', {})
                                    post_build_stages = ci_pipeline_details.get('postBuildStage', {})
                                    
                                    pre_build_tasks = {}
                                    post_build_tasks = {}
                                    pre_build_tasks['tasks']=[]
                                    post_build_tasks['tasks']=[]

                                    # Process pre-build stages
                                    if pre_build_stages.get('steps'):
                                        for step in pre_build_stages['steps']:
                                            if step.get('stepType') == 'REF_PLUGIN':
                                                config = {
                                                    'type': 'plugin',
                                                    'name': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('name')),
                                                    'task_name': step.get('name'), 
                                                    'version': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('pluginVersion')), # Not getting in payload
                                                    'input_variables': ({ var["name"]: var["value"] for var in step.get('pluginRefStepDetail').get('inputVariables', []) } if step.get('pluginRefStepDetail').get('inputVariables') else {})
                                                }
                                                # Remove empty values
                                                config = {k: v for k, v in config.items() if v}
                                                pre_build_tasks['tasks'].append(config)
                                            elif step.get('stepType') == 'INLINE':
                                                # Extract custom task configuration
                                                inline_detail = step.get('inlineStepDetail', {})
                                                config = {
                                                    'type': 'custom',
                                                    'task_name': step.get('name', ''),
                                                }
                                                if step.get('description'):
                                                    config['description'] = step['description']
                                                
                                                # Check if this is a container image task
                                                script_type = inline_detail.get('scriptType', 'SHELL')
                                                is_container_task = bool(inline_detail.get('containerImagePath')) or (script_type == 'CONTAINER_IMAGE')
                                                
                                                # Extract container image if present
                                                if is_container_task and inline_detail.get('containerImagePath'):
                                                    config['container_image'] = inline_detail['containerImagePath']
                                                
                                                # Extract script and convert escaped newlines to actual newlines
                                                if inline_detail.get('script'):
                                                    script = inline_detail['script']
                                                    script = self._format_script_for_yaml(script)
                                                    config['script'] = script
                                                
                                                # Extract script type if not default SHELL and not CONTAINER_IMAGE (handled by container_image field)
                                                if script_type and script_type != 'SHELL' and script_type != 'CONTAINER_IMAGE':
                                                    config['script_type'] = script_type
                                                
                                                # Extract input variables
                                                input_vars = inline_detail.get('inputVariables', [])
                                                if input_vars:
                                                    formatted_input_vars = []
                                                    for var in input_vars:
                                                        var_config = {
                                                            'key': var.get('name', ''),
                                                            'value': var.get('value', ''),
                                                            'type': var.get('format', 'STRING')
                                                        }
                                                        if var.get('description'):
                                                            var_config['description'] = var['description']
                                                        formatted_input_vars.append(var_config)
                                                    config['input_variables'] = formatted_input_vars
                                                
                                                # For container image tasks, extract container-specific fields
                                                if is_container_task:
                                                    # Extract script mount path
                                                    if inline_detail.get('storeScriptAt'):
                                                        config['script_mount_path'] = inline_detail['storeScriptAt']
                                                    
                                                    # Extract mount code to container path
                                                    if inline_detail.get('mountCodeToContainerPath'):
                                                        config['script_mount_path_on_container'] = inline_detail['mountCodeToContainerPath']
                                                    
                                                    # Extract command and args
                                                    command_args_map = inline_detail.get('commandArgsMap', [])
                                                    if command_args_map and len(command_args_map) > 0:
                                                        first_cmd = command_args_map[0]
                                                        if first_cmd.get('command'):
                                                            config['command'] = first_cmd['command']
                                                        if first_cmd.get('args'):
                                                            config['args'] = first_cmd['args']
                                                    
                                                    # Extract port mappings
                                                    port_map = inline_detail.get('portMap', [])
                                                    if port_map:
                                                        ports_mappings = []
                                                        for port in port_map:
                                                            local_port = port.get('portOnLocal', '')
                                                            container_port = port.get('portOnContainer', '')
                                                            if local_port and container_port:
                                                                ports_mappings.append(f"{local_port}:{container_port}")
                                                        if ports_mappings:
                                                            config['ports_mappings'] = ports_mappings
                                                    
                                                    # Extract directory mappings
                                                    mount_path_map = inline_detail.get('mountPathMap', [])
                                                    if mount_path_map:
                                                        directory_mappings = []
                                                        for mapping in mount_path_map:
                                                            host_path = mapping.get('filePathOnDisk', '')
                                                            container_path = mapping.get('filePathOnContainer', '')
                                                            if host_path and container_path:
                                                                directory_mappings.append(f"{host_path}:{container_path}")
                                                        if directory_mappings:
                                                            config['directory_mappings'] = directory_mappings
                                                else:
                                                    # For non-container tasks, extract output variables and conditions
                                                    output_vars = inline_detail.get('outputVariables', [])
                                                    if output_vars:
                                                        formatted_output_vars = []
                                                        for var in output_vars:
                                                            var_config = {
                                                                'key': var.get('name', ''),
                                                                'type': var.get('format', 'STRING')
                                                            }
                                                            if var.get('description'):
                                                                var_config['description'] = var['description']
                                                            formatted_output_vars.append(var_config)
                                                        config['output_variables'] = formatted_output_vars
                                                    
                                                    # Extract conditions
                                                    condition_details = inline_detail.get('conditionDetails', [])
                                                    if condition_details:
                                                        trigger_conditions = []
                                                        pass_conditions = []
                                                        fail_conditions = []
                                                        
                                                        for cond in condition_details:
                                                            cond_config = {
                                                                'key': cond.get('conditionOnVariable', ''),
                                                                'operator': cond.get('conditionOperator', ''),
                                                                'value': cond.get('conditionalValue', '')
                                                            }
                                                            
                                                            cond_type = cond.get('conditionType', '')
                                                            if cond_type == 'TRIGGER':
                                                                trigger_conditions.append(cond_config)
                                                            elif cond_type == 'PASS':
                                                                pass_conditions.append(cond_config)
                                                            elif cond_type == 'FAIL':
                                                                fail_conditions.append(cond_config)
                                                        
                                                        if trigger_conditions:
                                                            config['trigger_conditions'] = trigger_conditions
                                                        if pass_conditions:
                                                            config['pass_conditions'] = pass_conditions
                                                        if fail_conditions:
                                                            config['fail_conditions'] = fail_conditions
                                                
                                                # Extract output directory paths
                                                if step.get('outputDirectoryPath'):
                                                    config['output_directory_paths'] = step['outputDirectoryPath']
                                                
                                                pre_build_tasks['tasks'].append(config)
                                    # Process post-build stages
                                    if post_build_stages.get('steps'):
                                        for step in post_build_stages['steps']:
                                            if step.get('stepType') == 'REF_PLUGIN':
                                                config = {
                                                    'type': 'plugin',
                                                    'name': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('name')),
                                                    'task_name': step.get('name'), 
                                                    'version': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('pluginVersion')), # Not getting in payload
                                                    'input_variables': ({ var["name"]: var["value"] for var in step.get('pluginRefStepDetail').get('inputVariables', []) } if step.get('pluginRefStepDetail').get('inputVariables') else {})
                                                }
                                                # Remove empty values
                                                config = {k: v for k, v in config.items() if v}
                                                post_build_tasks['tasks'].append(config)
                                            elif step.get('stepType') == 'INLINE':
                                                # Extract custom task configuration
                                                inline_detail = step.get('inlineStepDetail', {})
                                                config = {
                                                    'type': 'custom',
                                                    'task_name': step.get('name', ''),
                                                }
                                                if step.get('description'):
                                                    config['description'] = step['description']
                                                
                                                # Check if this is a container image task
                                                script_type = inline_detail.get('scriptType', 'SHELL')
                                                is_container_task = bool(inline_detail.get('containerImagePath')) or (script_type == 'CONTAINER_IMAGE')
                                                
                                                # Extract container image if present
                                                if is_container_task and inline_detail.get('containerImagePath'):
                                                    config['container_image'] = inline_detail['containerImagePath']
                                                
                                                # Extract script and convert escaped newlines to actual newlines
                                                if inline_detail.get('script'):
                                                    script = inline_detail['script']
                                                    script = self._format_script_for_yaml(script)
                                                    config['script'] = script
                                                
                                                # Extract script type if not default SHELL and not CONTAINER_IMAGE (handled by container_image field)
                                                if script_type and script_type != 'SHELL' and script_type != 'CONTAINER_IMAGE':
                                                    config['script_type'] = script_type
                                                
                                                # Extract input variables
                                                input_vars = inline_detail.get('inputVariables', [])
                                                if input_vars:
                                                    formatted_input_vars = []
                                                    for var in input_vars:
                                                        var_config = {
                                                            'key': var.get('name', ''),
                                                            'value': var.get('value', ''),
                                                            'type': var.get('format', 'STRING')
                                                        }
                                                        if var.get('description'):
                                                            var_config['description'] = var['description']
                                                        formatted_input_vars.append(var_config)
                                                    config['input_variables'] = formatted_input_vars
                                                
                                                # For container image tasks, extract container-specific fields
                                                if is_container_task:
                                                    # Extract script mount path
                                                    if inline_detail.get('storeScriptAt'):
                                                        config['script_mount_path'] = inline_detail['storeScriptAt']
                                                    
                                                    # Extract mount code to container path
                                                    if inline_detail.get('mountCodeToContainerPath'):
                                                        config['script_mount_path_on_container'] = inline_detail['mountCodeToContainerPath']
                                                    
                                                    # Extract command and args
                                                    command_args_map = inline_detail.get('commandArgsMap', [])
                                                    if command_args_map and len(command_args_map) > 0:
                                                        first_cmd = command_args_map[0]
                                                        if first_cmd.get('command'):
                                                            config['command'] = first_cmd['command']
                                                        if first_cmd.get('args'):
                                                            config['args'] = first_cmd['args']
                                                    
                                                    # Extract port mappings
                                                    port_map = inline_detail.get('portMap', [])
                                                    if port_map:
                                                        ports_mappings = []
                                                        for port in port_map:
                                                            local_port = port.get('portOnLocal', '')
                                                            container_port = port.get('portOnContainer', '')
                                                            if local_port and container_port:
                                                                ports_mappings.append(f"{local_port}:{container_port}")
                                                        if ports_mappings:
                                                            config['ports_mappings'] = ports_mappings
                                                    
                                                    # Extract directory mappings
                                                    mount_path_map = inline_detail.get('mountPathMap', [])
                                                    if mount_path_map:
                                                        directory_mappings = []
                                                        for mapping in mount_path_map:
                                                            host_path = mapping.get('filePathOnDisk', '')
                                                            container_path = mapping.get('filePathOnContainer', '')
                                                            if host_path and container_path:
                                                                directory_mappings.append(f"{host_path}:{container_path}")
                                                        if directory_mappings:
                                                            config['directory_mappings'] = directory_mappings
                                                else:
                                                    # For non-container tasks, extract output variables and conditions
                                                    # Extract output variables
                                                    output_vars = inline_detail.get('outputVariables', [])
                                                    if output_vars:
                                                        formatted_output_vars = []
                                                        for var in output_vars:
                                                            var_config = {
                                                                'key': var.get('name', ''),
                                                                'type': var.get('format', 'STRING')
                                                            }
                                                            if var.get('description'):
                                                                var_config['description'] = var['description']
                                                            formatted_output_vars.append(var_config)
                                                        config['output_variables'] = formatted_output_vars
                                                    
                                                    # Extract conditions
                                                    condition_details = inline_detail.get('conditionDetails', [])
                                                    if condition_details:
                                                        trigger_conditions = []
                                                        pass_conditions = []
                                                        fail_conditions = []
                                                        
                                                        for cond in condition_details:
                                                            cond_config = {
                                                                'key': cond.get('conditionOnVariable', ''),
                                                                'operator': cond.get('conditionOperator', ''),
                                                                'value': cond.get('conditionalValue', '')
                                                            }
                                                            
                                                            cond_type = cond.get('conditionType', '')
                                                            if cond_type == 'TRIGGER':
                                                                trigger_conditions.append(cond_config)
                                                            elif cond_type == 'PASS':
                                                                pass_conditions.append(cond_config)
                                                            elif cond_type == 'FAIL':
                                                                fail_conditions.append(cond_config)
                                                        
                                                        if trigger_conditions:
                                                            config['trigger_conditions'] = trigger_conditions
                                                        if pass_conditions:
                                                            config['pass_conditions'] = pass_conditions
                                                        if fail_conditions:
                                                            config['fail_conditions'] = fail_conditions
                                                
                                                # Extract output directory paths
                                                if step.get('outputDirectoryPath'):
                                                    config['output_directory_paths'] = step['outputDirectoryPath']
                                                
                                                post_build_tasks['tasks'].append(config)
                                    
                                    if pre_build_tasks:
                                        ci_pipeline_config['pre_build_configs'] = pre_build_tasks
                                    if post_build_tasks:
                                        ci_pipeline_config['post_build_configs'] = post_build_tasks
                                    
                                    workflow_info['ci_pipeline'] = ci_pipeline_config
                        
                        # Find CD pipelines in this workflow
                        cd_pipelines = []
                        for node in tree:
                            if node.get('type') == 'CD_PIPELINE':
                                cd_pipeline_id = node.get('componentId')
                                # Get CD pipeline details
                                cd_pipeline_result = self.utils.get_cd_pipeline_details(app_id, cd_pipeline_id)
                                if cd_pipeline_result['success']:
                                    cd_pipeline_details = cd_pipeline_result['pipeline_details']
                                    
                                    cd_pipeline_config = {
                                        'name': cd_pipeline_details.get('name'),
                                        'environment_name': cd_pipeline_details.get('environmentName'),
                                        'is_manual': cd_pipeline_details.get('isManual', False),
                                        'deployment_type': cd_pipeline_details.get('deploymentAppType', 'helm').lower()
                                    }
                                    
                                    # Extract deployment strategies
                                    strategies = cd_pipeline_details.get('strategies', [])
                                    if strategies:
                                        deployment_strategies = []
                                        for strategy in strategies:
                                            strategy_config = {
                                                'name': strategy.get('deploymentTemplate'),
                                                'strategy': (
                                                    {
                                                        k: v
                                                        for k, v in strategy.get('config', {}).get('deployment', {}).get('strategy', {}).get('rolling', {}).items()
                                                    }
                                                    if strategy.get('deploymentTemplate') == "ROLLING"
                                                    else {}
                                                ),
                                                'default': strategy.get('default', False)
                                            }
                                            deployment_strategies.append(strategy_config)
                                        cd_pipeline_config['deployment_strategies'] = deployment_strategies
                                    
                                    # Extract pre-CD and post-CD configurations
                                    pre_cd_stages = cd_pipeline_details.get('preDeployStage', {})
                                    post_cd_stages = cd_pipeline_details.get('postDeployStage', {})
                                    
                                    pre_cd_tasks = {}
                                    post_cd_tasks = {}
                                    pre_cd_tasks['tasks']=[]
                                    post_cd_tasks['tasks']=[]
                                    
                                    # Process pre-CD stages
                                    if pre_cd_stages.get('steps'):
                                        for step in pre_cd_stages['steps']:
                                            if step.get('stepType') == 'REF_PLUGIN':
                                                config = {
                                                    'type': 'plugin',
                                                    'name': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('name')),
                                                    'task_name': step.get('name'), 
                                                    'version': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('pluginVersion')), # Not getting in payload
                                                    'input_variables': ({ var["name"]: var["value"] for var in step.get('pluginRefStepDetail').get('inputVariables', []) } if step.get('pluginRefStepDetail').get('inputVariables') else {})
                                                }
                                                # Remove empty values
                                                config = {k: v for k, v in config.items() if v}
                                                pre_cd_tasks['tasks'].append(config)
                                            elif step.get('stepType') == 'INLINE':
                                                # Extract custom task configuration
                                                inline_detail = step.get('inlineStepDetail', {})
                                                config = {
                                                    'type': 'custom',
                                                    'task_name': step.get('name', ''),
                                                }
                                                if step.get('description'):
                                                    config['description'] = step['description']
                                                
                                                # Check if this is a container image task
                                                script_type = inline_detail.get('scriptType', 'SHELL')
                                                is_container_task = bool(inline_detail.get('containerImagePath')) or (script_type == 'CONTAINER_IMAGE')
                                                
                                                # Extract container image if present
                                                if is_container_task and inline_detail.get('containerImagePath'):
                                                    config['container_image'] = inline_detail['containerImagePath']
                                                
                                                # Extract script and convert escaped newlines to actual newlines
                                                if inline_detail.get('script'):
                                                    script = inline_detail['script']
                                                    script = self._format_script_for_yaml(script)
                                                    config['script'] = script
                                                
                                                # Extract script type if not default SHELL and not CONTAINER_IMAGE (handled by container_image field)
                                                if script_type and script_type != 'SHELL' and script_type != 'CONTAINER_IMAGE':
                                                    config['script_type'] = script_type
                                                
                                                # Extract input variables
                                                input_vars = inline_detail.get('inputVariables', [])
                                                if input_vars:
                                                    formatted_input_vars = []
                                                    for var in input_vars:
                                                        var_config = {
                                                            'key': var.get('name', ''),
                                                            'value': var.get('value', ''),
                                                            'type': var.get('format', 'STRING')
                                                        }
                                                        if var.get('description'):
                                                            var_config['description'] = var['description']
                                                        formatted_input_vars.append(var_config)
                                                    config['input_variables'] = formatted_input_vars
                                                
                                                # For container image tasks, extract container-specific fields
                                                if is_container_task:
                                                    # Extract script mount path
                                                    if inline_detail.get('storeScriptAt'):
                                                        config['script_mount_path'] = inline_detail['storeScriptAt']
                                                    
                                                    # Extract mount code to container path
                                                    if inline_detail.get('mountCodeToContainerPath'):
                                                        config['script_mount_path_on_container'] = inline_detail['mountCodeToContainerPath']
                                                    
                                                    # Extract command and args
                                                    command_args_map = inline_detail.get('commandArgsMap', [])
                                                    if command_args_map and len(command_args_map) > 0:
                                                        first_cmd = command_args_map[0]
                                                        if first_cmd.get('command'):
                                                            config['command'] = first_cmd['command']
                                                        if first_cmd.get('args'):
                                                            config['args'] = first_cmd['args']
                                                    
                                                    # Extract port mappings
                                                    port_map = inline_detail.get('portMap', [])
                                                    if port_map:
                                                        ports_mappings = []
                                                        for port in port_map:
                                                            local_port = port.get('portOnLocal', '')
                                                            container_port = port.get('portOnContainer', '')
                                                            if local_port and container_port:
                                                                ports_mappings.append(f"{local_port}:{container_port}")
                                                        if ports_mappings:
                                                            config['ports_mappings'] = ports_mappings
                                                    
                                                    # Extract directory mappings
                                                    mount_path_map = inline_detail.get('mountPathMap', [])
                                                    if mount_path_map:
                                                        directory_mappings = []
                                                        for mapping in mount_path_map:
                                                            host_path = mapping.get('filePathOnDisk', '')
                                                            container_path = mapping.get('filePathOnContainer', '')
                                                            if host_path and container_path:
                                                                directory_mappings.append(f"{host_path}:{container_path}")
                                                        if directory_mappings:
                                                            config['directory_mappings'] = directory_mappings
                                                else:
                                                    # For non-container tasks, extract output variables and conditions
                                                    # Extract output variables
                                                    output_vars = inline_detail.get('outputVariables', [])
                                                    if output_vars:
                                                        formatted_output_vars = []
                                                        for var in output_vars:
                                                            var_config = {
                                                                'key': var.get('name', ''),
                                                                'type': var.get('format', 'STRING')
                                                            }
                                                            if var.get('description'):
                                                                var_config['description'] = var['description']
                                                            formatted_output_vars.append(var_config)
                                                        config['output_variables'] = formatted_output_vars
                                                    
                                                    # Extract conditions
                                                    condition_details = inline_detail.get('conditionDetails', [])
                                                    if condition_details:
                                                        trigger_conditions = []
                                                        pass_conditions = []
                                                        fail_conditions = []
                                                        
                                                        for cond in condition_details:
                                                            cond_config = {
                                                                'key': cond.get('conditionOnVariable', ''),
                                                                'operator': cond.get('conditionOperator', ''),
                                                                'value': cond.get('conditionalValue', '')
                                                            }
                                                            
                                                            cond_type = cond.get('conditionType', '')
                                                            if cond_type == 'TRIGGER':
                                                                trigger_conditions.append(cond_config)
                                                            elif cond_type == 'PASS':
                                                                pass_conditions.append(cond_config)
                                                            elif cond_type == 'FAIL':
                                                                fail_conditions.append(cond_config)
                                                        
                                                        if trigger_conditions:
                                                            config['trigger_conditions'] = trigger_conditions
                                                        if pass_conditions:
                                                            config['pass_conditions'] = pass_conditions
                                                        if fail_conditions:
                                                            config['fail_conditions'] = fail_conditions
                                                
                                                # Extract output directory paths
                                                if step.get('outputDirectoryPath'):
                                                    config['output_directory_paths'] = step['outputDirectoryPath']
                                                
                                                pre_cd_tasks['tasks'].append(config)
                                    # Process post-CD stages
                                    if post_cd_stages.get('steps'):
                                        for step in post_cd_stages['steps']:
                                            if step.get('stepType') == 'REF_PLUGIN':
                                                config = {
                                                    'type': 'plugin',
                                                    'name': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('name')),
                                                    'task_name': step.get('name'), 
                                                    'version': (self.workflow.get_plugins_details_id(app_id, [step.get('pluginRefStepDetail', {}).get('pluginId')]).get('pluginVersion')), # Not getting in payload
                                                    'input_variables': ({ var["name"]: var["value"] for var in step.get('pluginRefStepDetail').get('inputVariables', []) } if step.get('pluginRefStepDetail').get('inputVariables') else {})
                                                }

                                                config = {k: v for k, v in config.items() if v}
                                                post_cd_tasks['tasks'].append(config)
                                            elif step.get('stepType') == 'INLINE':
                                                # Extract custom task configuration
                                                inline_detail = step.get('inlineStepDetail', {})
                                                config = {
                                                    'type': 'custom',
                                                    'task_name': step.get('name', ''),
                                                }
                                                if step.get('description'):
                                                    config['description'] = step['description']
                                                
                                                # Check if this is a container image task
                                                script_type = inline_detail.get('scriptType', 'SHELL')
                                                is_container_task = bool(inline_detail.get('containerImagePath')) or (script_type == 'CONTAINER_IMAGE')
                                                
                                                # Extract container image if present
                                                if is_container_task and inline_detail.get('containerImagePath'):
                                                    config['container_image'] = inline_detail['containerImagePath']
                                                
                                                # Extract script and convert escaped newlines to actual newlines
                                                if inline_detail.get('script'):
                                                    script = inline_detail['script']
                                                    script = self._format_script_for_yaml(script)
                                                    config['script'] = script
                                                
                                                # Extract script type if not default SHELL and not CONTAINER_IMAGE (handled by container_image field)
                                                if script_type and script_type != 'SHELL' and script_type != 'CONTAINER_IMAGE':
                                                    config['script_type'] = script_type
                                                
                                                # Extract input variables
                                                input_vars = inline_detail.get('inputVariables', [])
                                                if input_vars:
                                                    formatted_input_vars = []
                                                    for var in input_vars:
                                                        var_config = {
                                                            'key': var.get('name', ''),
                                                            'value': var.get('value', ''),
                                                            'type': var.get('format', 'STRING')
                                                        }
                                                        if var.get('description'):
                                                            var_config['description'] = var['description']
                                                        formatted_input_vars.append(var_config)
                                                    config['input_variables'] = formatted_input_vars
                                                
                                                # For container image tasks, extract container-specific fields
                                                if is_container_task:
                                                    # Extract script mount path
                                                    if inline_detail.get('storeScriptAt'):
                                                        config['script_mount_path'] = inline_detail['storeScriptAt']
                                                    
                                                    # Extract mount code to container path
                                                    if inline_detail.get('mountCodeToContainerPath'):
                                                        config['script_mount_path_on_container'] = inline_detail['mountCodeToContainerPath']
                                                    
                                                    # Extract command and args
                                                    command_args_map = inline_detail.get('commandArgsMap', [])
                                                    if command_args_map and len(command_args_map) > 0:
                                                        first_cmd = command_args_map[0]
                                                        if first_cmd.get('command'):
                                                            config['command'] = first_cmd['command']
                                                        if first_cmd.get('args'):
                                                            config['args'] = first_cmd['args']
                                                    
                                                    # Extract port mappings
                                                    port_map = inline_detail.get('portMap', [])
                                                    if port_map:
                                                        ports_mappings = []
                                                        for port in port_map:
                                                            local_port = port.get('portOnLocal', '')
                                                            container_port = port.get('portOnContainer', '')
                                                            if local_port and container_port:
                                                                ports_mappings.append(f"{local_port}:{container_port}")
                                                        if ports_mappings:
                                                            config['ports_mappings'] = ports_mappings
                                                    
                                                    # Extract directory mappings
                                                    mount_path_map = inline_detail.get('mountPathMap', [])
                                                    if mount_path_map:
                                                        directory_mappings = []
                                                        for mapping in mount_path_map:
                                                            host_path = mapping.get('filePathOnDisk', '')
                                                            container_path = mapping.get('filePathOnContainer', '')
                                                            if host_path and container_path:
                                                                directory_mappings.append(f"{host_path}:{container_path}")
                                                        if directory_mappings:
                                                            config['directory_mappings'] = directory_mappings
                                                else:
                                                    # For non-container tasks, extract output variables and conditions
                                                    # Extract output variables
                                                    output_vars = inline_detail.get('outputVariables', [])
                                                    if output_vars:
                                                        formatted_output_vars = []
                                                        for var in output_vars:
                                                            var_config = {
                                                                'key': var.get('name', ''),
                                                                'type': var.get('format', 'STRING')
                                                            }
                                                            if var.get('description'):
                                                                var_config['description'] = var['description']
                                                            formatted_output_vars.append(var_config)
                                                        config['output_variables'] = formatted_output_vars
                                                    
                                                    # Extract conditions
                                                    condition_details = inline_detail.get('conditionDetails', [])
                                                    if condition_details:
                                                        trigger_conditions = []
                                                        pass_conditions = []
                                                        fail_conditions = []
                                                        
                                                        for cond in condition_details:
                                                            cond_config = {
                                                                'key': cond.get('conditionOnVariable', ''),
                                                                'operator': cond.get('conditionOperator', ''),
                                                                'value': cond.get('conditionalValue', '')
                                                            }
                                                            
                                                            cond_type = cond.get('conditionType', '')
                                                            if cond_type == 'TRIGGER':
                                                                trigger_conditions.append(cond_config)
                                                            elif cond_type == 'PASS':
                                                                pass_conditions.append(cond_config)
                                                            elif cond_type == 'FAIL':
                                                                fail_conditions.append(cond_config)
                                                        
                                                        if trigger_conditions:
                                                            config['trigger_conditions'] = trigger_conditions
                                                        if pass_conditions:
                                                            config['pass_conditions'] = pass_conditions
                                                        if fail_conditions:
                                                            config['fail_conditions'] = fail_conditions
                                                
                                                # Extract output directory paths
                                                if step.get('outputDirectoryPath'):
                                                    config['output_directory_paths'] = step['outputDirectoryPath']
                                                
                                                post_cd_tasks['tasks'].append(config)
                                    if pre_cd_tasks:
                                        cd_pipeline_config['pre_cd_tasks'] = pre_cd_tasks
                                    if post_cd_tasks:
                                        cd_pipeline_config['post_cd_tasks'] = post_cd_tasks
                                    
                                    env_configuration = {}

                                    # Env Detials
                                    env_id = cd_pipeline_details.get('environmentId')
                                    env_name = cd_pipeline_details.get('environmentName')

                                    chart_ref_id = OverrideDeploymentTemplateHandler.get_chart_ref_id_for_env(self.base_url, self.headers, app_id,env_id).get('chart_ref_id')

                                    env_configuration_result = self.override_config.get_env_configuration_template(app_id,env_id,chart_ref_id)['env_config_template']

                                    # If deployment template is overridden
                                    if env_configuration_result.get('IsOverride'):
                                        merge_strategy = "patch" if env_configuration_result.get('environmentConfig').get('envOverridePatchValues') else "replace"
                                        
                                        # To fetch respective override yaml
                                        if merge_strategy == "patch":
                                            override_template_yaml = env_configuration_result.get('environmentConfig').get('envOverridePatchValues')
                                        elif merge_strategy == "replace":
                                            override_template_yaml = env_configuration_result.get('environmentConfig').get('envOverrideValues')

                                        # Create filename based on app name and env name
                                        override_values_filename = f"override-{app_name}-{env_name}-values.yaml"
                                        
                                        # Write the values to the file
                                        with open(override_values_filename, 'w') as f:
                                            dump_yaml(override_template_yaml, stream=f)
                                        
                                        env_config_template = {
                                            'type': "override",
                                            'version': self.utils._get_chart_details_from_id(app_id,chart_ref_id).get("version"),
                                            "merge_strategy": merge_strategy,
                                            "show_application_metrics": env_configuration_result.get('appMetrics'),
                                            "values_path": override_values_filename
                                        }
                                    else:
                                        env_config_template = {
                                            'type': "inherit",
                                            'version': self.utils._get_chart_details_from_id(app_id,chart_ref_id).get("version"),
                                            "merge_strategy": "replace",
                                            "show_application_metrics": env_configuration_result.get('appMetrics'),
                                            "values_path": f"base-{app_name}-values.yaml"
                                        }
                                    env_configuration['deployment_template'] = env_config_template
                                    
                                    env_configuration['config_maps'] = []
                                    env_configuration['secrets'] = []
                                    try:
                                        env_level_cm_cs = self.override_config.env_override_cm_cs.get_override_cm_cs_list(app_id,env_id)
                                        if env_level_cm_cs['success']:
                                            env_level_cm_cs_list = env_level_cm_cs.get('result')
                                            envConfigmap = []
                                            if env_level_cm_cs_list.get('cm_list'):
                                                for cm_name in env_level_cm_cs_list['cm_list']:
                                                    env_cm_details_result = self.override_config.env_override_cm_cs.get_override_config_map_details(app_name,env_name,cm_name,env_level_cm_cs_list.get('resourceConfigId'))
                                                    if env_cm_details_result['success']:
                                                        # Remove global and overriden fields from secret
                                                        env_config_data = env_cm_details_result['config_map']
                                                        env_config_data.pop('global', None)
                                                        env_config_data.pop('overridden', None)
                                                        
                                                        # Remove subPath field if type is environment
                                                        if env_config_data.get('type') == 'environment':
                                                            env_config_data.pop('subPath', None)
                                                        
                                                        # Handle reverse logic for external secrets with mountPath and subPath
                                                        # Extract subPath from data object if special conditions are met
                                                        if (env_config_data.get('external') is True and 
                                                            env_config_data.get('mountPath') and 
                                                            env_config_data.get('data')):
                                                            
                                                            # Check if any key in data has an empty string value (indicating it was a subPath)
                                                            sub_path_key = None
                                                            for key, value in env_config_data['data'].items():
                                                                if value == "":
                                                                    sub_path_key = key
                                                                    break
                                                            
                                                            if sub_path_key:
                                                                # Set the subPath field and remove the empty entry from data
                                                                env_config_data['subPath'] = sub_path_key
                                                                del env_config_data['data'][sub_path_key]
                                                                
                                                                # If data becomes empty after removal, remove the data field entirely
                                                                if not env_config_data['data']:
                                                                    env_config_data.pop('data', None)
                                                        cm_is_external = env_config_data.get('external')
                                                        cm_merge_strategy = env_config_data.get('mergeStrategy')
                                                        override_cm_yaml = {}

                                                        if cm_merge_strategy == 'patch' and not cm_is_external:
                                                            env_config_data.pop('data')
                                                            env_config_data.pop('defaultData')
                                                            override_cm_yaml = env_config_data.get('patchData')
                                                            env_config_data.pop('patchData')
                                                        elif cm_merge_strategy == 'replace' and not cm_is_external:
                                                            env_config_data.pop('defaultData')
                                                            override_cm_yaml = env_config_data.get('data')
                                                            env_config_data.pop('data')
                                                        elif cm_merge_strategy == '' and not cm_is_external:
                                                            override_cm_yaml = env_config_data.get('data')
                                                            env_config_data.pop('data')

                                                        if override_cm_yaml:
                                                            # Create filename based on app name and env name
                                                            override_cm_filename = f"override-cm-{cm_name}-{app_name}-{env_name}-values.yaml"
                                                            env_config_data['from_file'] = override_cm_filename
                                                            # Write the values to the file
                                                            with open(override_cm_filename, 'w') as f:
                                                                dump_yaml(override_cm_yaml, stream=f)

                                                        envConfigmap.append(env_config_data)
                                            envSecrets = []
                                            if env_level_cm_cs_list.get('cs_list'):
                                                for secret_name in env_level_cm_cs_list['cs_list']:
                                                    env_secret_details_result = self.override_config.env_override_cm_cs.get_override_secret_details(app_name,env_name,secret_name,env_level_cm_cs_list.get('resourceConfigId'))
                                                    if env_secret_details_result['success']:
                                                        # Remove global and overriden fields from secret
                                                        env_secret_data = env_secret_details_result['secret']
                                                        env_secret_data.pop('global', None)
                                                        env_secret_data.pop('overridden', None)
                                                        
                                                        # Remove subPath field if type is environment
                                                        if env_secret_data.get('type') == 'environment':
                                                            env_secret_data.pop('subPath', None)
                                                        
                                                        # Handle reverse logic for external secrets with mountPath and subPath
                                                        # Extract subPath from data object if special conditions are met
                                                        if (env_secret_data.get('external') is True and 
                                                            env_secret_data.get('mountPath') and 
                                                            env_secret_data.get('data')):
                                                            
                                                            # Check if any key in data has an empty string value (indicating it was a subPath)
                                                            sub_path_key = None
                                                            for key, value in env_secret_data['data'].items():
                                                                if value == "":
                                                                    sub_path_key = key
                                                                    break
                                                            
                                                            if sub_path_key:
                                                                # Set the subPath field and remove the empty entry from data
                                                                env_secret_data['subPath'] = sub_path_key
                                                                del env_secret_data['data'][sub_path_key]
                                                                
                                                                # If data becomes empty after removal, remove the data field entirely
                                                                if not env_secret_data['data']:
                                                                    env_secret_data.pop('data', None)
                                                        override_secret_yaml = {} 
                                                        is_external = env_secret_data.get('external')
                                                        secret_merge_strategy = env_secret_data.get('mergeStrategy')
                                                        if secret_merge_strategy == 'patch' and not is_external:
                                                            env_secret_data.pop('data')
                                                            env_secret_data['data'] = env_secret_data.get('patchData')
                                                            env_secret_data.pop('patchData')

                                                        # Base64 decoding the value    
                                                        if 'data' in env_secret_data and env_secret_data['data']:
                                                            env_decoded_data = {}
                                                            for key, encoded_value in env_secret_data['data'].items():
                                                                try:
                                                                    import base64
                                                                    decoded_value = base64.b64decode(encoded_value).decode('utf-8')
                                                                    env_decoded_data[key] = decoded_value
                                                                except Exception as e:
                                                                    print(f"Warning: Failed to decode base64 value for key '{key}': {e}")
                                                                    env_decoded_data[key] = encoded_value  # Keep original if decoding fails
                                                            env_secret_data['data'] = env_decoded_data
                                                        
                                                        override_secret_yaml = env_secret_data['data']
                                                        env_secret_data.pop('data')

                                                        if override_secret_yaml:
                                                            # Create filename based on app name and env name
                                                            override_secret_filename = f"override-secret-{secret_name}-{app_name}-{env_name}-values.yaml"
                                                            env_secret_data['from_file'] = override_secret_filename
                                                            
                                                            # Write the values to the file
                                                            with open(override_secret_filename, 'w') as f:
                                                                dump_yaml(override_secret_yaml, stream=f)
                                                        envSecrets.append(env_secret_data)

                                            if envConfigmap:
                                                env_configuration['config_maps'] = envConfigmap
                                            if envSecrets:
                                                env_configuration['secrets'] = envSecrets
                                    except Exception as e:
                                        print(f"Warning: Could not fetch Env level config maps and secrets: {str(e)}")
                                                                            

                                    cd_pipeline_config['env_configuration'] = env_configuration

                                    cd_pipelines.append(cd_pipeline_config)
                        
                        if cd_pipelines:
                            workflow_info['cd_pipelines'] = cd_pipelines
                        
                        if workflow_info:  # Only add if we have pipeline data
                            workflows_data.append(workflow_info)
                
                if workflows_data:
                    config_data['workflows'] = workflows_data
                    
            except Exception as e:
                print(f"Warning: Could not fetch workflows: {str(e)}")
            
            # Clean up the config data by removing empty values
            cleaned_config_data = self.utils.remove_empty_values(config_data)
            
            
            
            return {
                'success': True,
                'config_data': cleaned_config_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Exception occurred: {str(e)}'
            }
