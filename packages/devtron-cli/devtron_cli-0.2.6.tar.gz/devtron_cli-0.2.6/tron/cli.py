import click
import yaml
import sys
import os
from tron.devtron_api import DevtronApplication
from tron.utils import CustomDumper, dump_yaml


def validate_devtron_credentials(devtron_url, api_token):
    """Validate Devtron URL and API token."""
    # Get Devtron URL and API token from command line args or environment variables
    devtron_url = devtron_url or os.environ.get('DEVTRON_URL')
    api_token = api_token or os.environ.get('DEVTRON_API_TOKEN')
    
    # Check if Devtron URL and API token are provided for actions that require them
    if not devtron_url:
        click.echo("Error: Devtron URL is required. Please provide it via --devtron-url option or DEVTRON_URL environment variable.", err=True)
        sys.exit(1)
    if not api_token:
        click.echo("Error: API token is required. Please provide it via --api-token option or DEVTRON_API_TOKEN environment variable.", err=True)
        sys.exit(1)
    
    return devtron_url, api_token


def load_config_and_initialize_api(config_path, devtron_url, api_token):
    """Load configuration and initialize Devtron API client."""
    # Check if config file exists (if required)
    if config_path and not os.path.exists(config_path):
        click.echo(f"Error: Config file '{config_path}' not found.", err=True)
        sys.exit(1)
    
    # Load YAML configuration (if required)
    config_data = None
    if config_path:
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            click.echo(f"Error loading config file: {e}", err=True)
            sys.exit(1)
    
    # Validate Devtron credentials
    devtron_url, api_token = validate_devtron_credentials(devtron_url, api_token)
    
    # Initialize Devtron API client
    try:
        devtron_api = DevtronApplication(
            base_url=devtron_url,
            api_token=api_token
        )
    except ConnectionError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: An unexpected error occurred during environment validation: {e}", err=True)
        sys.exit(1)
    
    return config_data, devtron_api


# Define global options as a decorator with optional parameters
def global_options(func):
    """Decorator to add global options to commands."""
    func = click.option('--config', '-c', required=False, help='Path to the YAML configuration file')(func)
    func = click.option('--devtron-url', '-u', help='Devtron URL (can also be set via DEVTRON_URL environment variable)')(func)
    func = click.option('--api-token', '-t', help='API token (can also be set via DEVTRON_API_TOKEN environment variable)')(func)
    return func


@click.group(invoke_without_command=True, context_settings={'help_option_names': ['-h', '--help']})
@global_options
@click.option('--version', '-v', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, config, devtron_url, api_token, version):
    """CLI tool for automating Devtron infrastructure and application management."""
    if version:
        # Use simple version file approach that works with PyInstaller
        try:
            from tron.version import __version__
            click.echo(f"tron version {__version__}")
        except:
            # Fallback to hardcoded version if import fails
            click.echo("tron version 0.2.6")
        ctx.exit()
    
    ctx.ensure_object(dict)
    # Store options in context for subcommands to access
    ctx.obj['config'] = config
    ctx.obj['devtron_url'] = devtron_url
    ctx.obj['api_token'] = api_token


def get_option_value(ctx, option_name, subcommand_value=None):
    """Get option value from subcommand or main command context."""
    # If provided directly to subcommand, use that
    if subcommand_value is not None:
        return subcommand_value
    # Otherwise, try to get from context
    return ctx.obj.get(option_name)


def validate_and_initialize_api(ctx, config=None, devtron_url=None, api_token=None):
    """Validate required options and initialize API client."""
    # Get values from subcommand or context
    config_path = get_option_value(ctx, 'config', config)
    url = get_option_value(ctx, 'devtron_url', devtron_url)
    token = get_option_value(ctx, 'api_token', api_token)
    
    # If not found in context, try parent context (for nested calls)
    if not config_path and ctx.parent:
        config_path = ctx.parent.obj.get('config')
        url = url or ctx.parent.obj.get('devtron_url')
        token = token or ctx.parent.obj.get('api_token')
    
    return load_config_and_initialize_api(config_path, url, token)


@main.command()
@global_options
@click.pass_context
def create_app(ctx, config, devtron_url, api_token):
    """Create a new application in Devtron."""
    config_data, devtron_api = validate_and_initialize_api(ctx, config, devtron_url, api_token)
    ctx.obj['config_data'] = config_data
    ctx.obj['devtron_api'] = devtron_api
    
    # Validate app_name if present in config
    app_name = config_data.get('app_name') if config_data else None
    if app_name:
        import re
        # Check length (3-30 characters)
        if len(app_name) < 3:
            click.echo("Error: Application name must be at least 3 characters long.", err=True)
            sys.exit(1)
        if len(app_name) > 30:
            click.echo("Error: Application name can't be more than 30 characters long.", err=True)
            sys.exit(1)
        
        # Check regex pattern: '^[a-z][a-z0-9-]*[a-z0-9]$'
        pattern = re.compile(r'^[a-z][a-z0-9-]*[a-z0-9]$')
        if not pattern.match(app_name):
            click.echo("Error: Application name must start with a lowercase letter, end with a lowercase letter or digit, and can only contain lowercase letters, digits, and hyphens.", err=True)
            sys.exit(1)
    
    result = devtron_api.create_application(config_data)
    if result['success']:
        click.echo("All steps for create-app completed successfully!")
        click.echo(f"Application ID: {result['app_id']}")
    else:
        click.echo(f"Error creating application: {result['error']}", err=True)
        sys.exit(1)


@main.command()
@global_options
@click.option('--allow-deletion', is_flag=True, help='Confirm deletion (required for actual deletion)')
@click.pass_context
def update_app(ctx, config, devtron_url, api_token, allow_deletion):
    """Update an existing application in Devtron."""
    config_data, devtron_api = validate_and_initialize_api(ctx, config, devtron_url, api_token)
    ctx.obj['config_data'] = config_data
    ctx.obj['devtron_api'] = devtron_api
    
    result = devtron_api.update_application(config_data, allow_deletion)
    if result['success']:
        click.echo("Application updated successfully!")
    else:
        click.echo(f"Error updating application: {result['error']}", err=True)
        sys.exit(1)


@main.command()
@global_options
@click.option('--app', required=True, help='Name of the application to fetch')
@click.option('--output', '-o', help='Output file path to save YAML configuration')
@click.pass_context
def get_app(ctx, config, devtron_url, api_token, app, output):
    """Get application configuration from Devtron and output in YAML format."""
    # For get-app, we only need the base URL and API token, not a config file
    # Use the same validation pattern as other commands but ignore config
    _, devtron_api = validate_and_initialize_api(ctx, None, devtron_url, api_token)
    
    result = devtron_api.get_application(app)
    if result['success']:
        config_data = result['config_data']
        
        # Output in YAML format with proper multi-line string handling
        yaml_output = dump_yaml(config_data)
        
        if output:
            # Save to file
            try:
                with open(output, 'w') as f:
                    f.write(yaml_output)
                click.echo(f"Configuration saved to: {output}")
            except Exception as e:
                click.echo(f"Error saving to file {output}: {e}", err=True)
                sys.exit(1)
        else:
            # Output to console
            click.echo(yaml_output)
    else:
        click.echo(f"Error fetching application: {result['error']}", err=True)
        sys.exit(1)



@main.command()
@global_options
@click.option('--app', required=True, help='Name of the application to delete')
@click.option('--approve', is_flag=True, help='Confirm deletion (required for actual deletion)')
@click.pass_context
def delete_app(ctx, config, devtron_url, api_token, app, approve):
    """Delete an application and all its associated pipelines."""
    # For delete-app, we only need the base URL and API token, not a config file
    # Use the same validation pattern as other commands but ignore config
    _, devtron_api = validate_and_initialize_api(ctx, None, devtron_url, api_token)
    
    result = devtron_api.delete_application(app, approve)
    if result['success']:
        click.echo(result['message'])
    else:
        click.echo(f"Error deleting application: {result['error']}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
