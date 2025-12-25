import click
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
from .generators.microservice import MicroserviceGenerator
from .validators import ConfigValidator

@click.group()
@click.version_option()
def cli():
    """ND-SDK - Enterprise Framework & Code Generator"""
    pass

@cli.command()
@click.option('--interactive', '-i', is_flag=True, default=False,
              help='Interactive mode with prompts')
@click.option('--type', '-t',
              type=click.Choice(['microservice', 'batch-job', 'worker']),
              help='Project type (skip interactive if provided)')
@click.option('--output', '-o', default='nd-config.yaml',
              help='Output configuration file name')
def init(interactive, type, output):
    """Create a configuration file interactively or from template"""
    config_path = Path(output)
    if interactive:
        # Interactive mode
        click.clear()
        click.echo(click.style("✨ Welcome to ND-SDK Project Generator\n", fg='cyan', bold=True))
        # Step 1: Project basics
        click.echo(click.style("📋 Project Information", fg='yellow', bold=True))
        project_name = click.prompt('Project name', default='my-microservice')
        project_type = click.prompt(
            'Project type',
            type=click.Choice(['microservice', 'batch-job', 'worker']),
            default='microservice'
        )
        description = click.prompt('Description', default=f'Sample {project_type} with ND-SDK')
        version = click.prompt('Version', default='1.0.0')
        environment = click.prompt(
            'Environment',
            type=click.Choice(['development', 'staging', 'production']),
            default='development'
        )
        # Step 2: Python configuration
        click.echo(click.style("\n🐍 Python Configuration", fg='yellow', bold=True))
        python_version = click.prompt('Python version', default='3.8.10')
        add_packages = click.confirm('Add additional packages?', default=False)
        packages = []
        if add_packages:
            click.echo("Enter packages (empty line to finish):")
            while True:
                pkg = click.prompt('  Package', default='', show_default=False)
                if not pkg:
                    break
                packages.append(pkg)
        else:
            packages = ['gunicorn==20.1.0']
        config_data = {
            'project': {
                'name': project_name,
                'type': project_type,
                'description': description,
                'version': version,
                'environment': environment
            },
            'python': {
                'version': python_version,
                'packages': packages,
                'pre_install_commands': ['apt-get update']
            }
        }
        if project_type == 'microservice':
            # Web configuration
            click.echo(click.style("\n🌐 Web Configuration", fg='yellow', bold=True))
            url_prefix = click.prompt('API URL prefix', default='/api/v1')
            config_data['web'] = {'url_prefix': url_prefix}
            # Modules
            click.echo(click.style("\n📦 Configure Modules", fg='yellow', bold=True))
            # Observability
            enable_observability = click.confirm('Enable observability (logging, tracing, metrics)?', default=True)
            if enable_observability:
                log_level = click.prompt(
                    'Log level',
                    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
                    default='INFO'
                )
                config_data['modules'] = {
                    'observability': {
                        'enabled': True,
                        'logging': {
                            'enabled': True,
                            'level': log_level,
                            'provider': 'otel'
                        },
                        'tracing': {
                            'enabled': True,
                            'provider': 'otel'
                        },
                        'metrics': {
                            'enabled': True,
                            'provider': 'otel'
                        }
                    }
                }
            # Caching
            enable_caching = click.confirm('Enable caching?', default=True)
            if enable_caching:
                cache_provider = click.prompt(
                    'Cache provider',
                    type=click.Choice(['redis', 'inmemory']),
                    default='redis'
                )
                caching_config = {
                    'enabled': True,
                    'default_provider': cache_provider,
                    'providers': {}
                }
                if cache_provider == 'redis':
                    redis_host = click.prompt('Redis host', default='localhost')
                    redis_port = click.prompt('Redis port', default=6379, type=int)
                    caching_config['providers']['redis'] = {
                        'host': redis_host,
                        'port': redis_port
                    }
                    caching_config['providers']['inmemory'] = {'max_size': 1000}
                else:
                    max_size = click.prompt('Max cache size', default=1000, type=int)
                    caching_config['providers']['inmemory'] = {'max_size': max_size}
                if 'modules' not in config_data:
                    config_data['modules'] = {}
                config_data['modules']['caching'] = caching_config
            # Storage
            enable_storage = click.confirm('Enable storage?', default=False)
            if enable_storage:
                storage_providers = []
                if click.confirm('Use S3?', default=True):
                    storage_providers.append('s3')
                if click.confirm('Use Azure?', default=False):
                    storage_providers.append('azure')
                if 'modules' not in config_data:
                    config_data['modules'] = {}
                config_data['modules']['storage'] = {
                    'enabled': True,
                    'providers': storage_providers
                }
            # Web framework
            if 'modules' not in config_data:
                config_data['modules'] = {}
            config_data['modules']['web_framework'] = 'flask'
            # Exception handler
            config_data['modules']['exception_handler'] = {
                'enabled': True,
                'include_traceback': True
            }
            # Endpoints
            click.echo(click.style("\n🔗 Configure Endpoints", fg='yellow', bold=True))
            add_health = click.confirm('Add health check endpoint?', default=True)
            endpoints = []
            if add_health:
                endpoints.append({
                    'name': 'health_check',
                    'path': '/health',
                    'method': 'GET',
                    'description': 'Health check endpoint',
                    'params': [],
                    'cache': {'enabled': False}
                })
            if click.confirm('Add sample endpoint?', default=True):
                sample_name = click.prompt('Endpoint name', default='sample_endpoint')
                sample_path = click.prompt('Path', default=f'/{sample_name}')
                sample_method = click.prompt(
                    'Method',
                    type=click.Choice(['GET', 'POST', 'PUT', 'DELETE']),
                    default='GET'
                )
                endpoints.append({
                    'name': sample_name,
                    'path': sample_path,
                    'method': sample_method,
                    'description': f'Sample {sample_method} endpoint',
                    'input_type': 'json' if sample_method != 'GET' else 'form',
                    'params': [
                        {
                            'name': 'sample_param',
                            'type': 'str',
                            'required': True,
                            'alias': 'sampleParam',
                            'min_length': 3,
                            'max_length': 500
                        }
                    ],
                    'cache': {'enabled': False}
                })
            config_data['endpoints'] = endpoints
            # Volume
            if click.confirm('Add volume mount paths?', default=False):
                config_data['volume'] = {
                    'mount_paths': ['/mnt/PyFramework']
                }
        elif project_type == 'batch-job':
            config_data['modules'] = {
                'observability': {
                    'enabled': True,
                    'logging': {
                        'enabled': True,
                        'level': 'INFO'
                    }
                },
                'storage': {
                    'enabled': True,
                    'providers': ['s3']
                }
            }
            config_data['jobs'] = [
                {
                    'name': 'data_processor',
                    'schedule': '0 0 * * *',
                    'description': 'Process daily data',
                    'steps': [
                        {'name': 'extract', 'type': 'extract'},
                        {'name': 'transform', 'type': 'transform'},
                        {'name': 'load', 'type': 'load'}
                    ]
                }
            ]
        elif project_type == 'worker':
            config_data['modules'] = {
                'observability': {'enabled': True},
                'queue': {
                    'enabled': True,
                    'provider': 'rabbitmq'
                }
            }
            config_data['tasks'] = [
                {'name': 'process_email', 'queue': 'emails', 'retry': 3},
                {'name': 'generate_report', 'queue': 'reports', 'retry': 5}
            ]
        # Save config
        if config_path.exists():
            if not click.confirm(f'{output} already exists. Overwrite?', abort=True):
                return
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, indent=2)
        click.echo(click.style(f"\n✓ Created {output}", fg='green', bold=True))
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Review and edit {output}")
        click.echo(f"  2. nd-sdk generate -c {output}")
    else:
        # Template mode (original behavior)
        if not type:
            type = 'microservice'
        templates = {
            'microservice': MICROSERVICE_TEMPLATE,
            'batch-job': BATCH_JOB_TEMPLATE,
            'worker': WORKER_TEMPLATE,
        }
        if config_path.exists():
            if not click.confirm(f'{output} already exists. Overwrite?', abort=True):
                return
        with open(config_path, 'w') as f:
            f.write(templates[type].strip())
        click.echo(click.style(f"✓ Created {output}", fg='green'))
        click.echo(f"\nEdit the configuration file and run:")
        click.echo(f"  nd-sdk generate -c {output}")

@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), required=True,
              help='Path to configuration YAML file')
@click.option('--output', '-o', type=click.Path(), default='.',
              help='Output directory for generated project')
@click.option('--force', '-f', is_flag=True,
              help='Force overwrite if project exists')
def generate(config, output, force):
    """Generate project from configuration file"""
    try:
        # Load and validate config
        click.echo(f"Loading configuration from {config}...")
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        # Validate configuration
        validator = ConfigValidator()
        is_valid, errors = validator.validate(config_data)
        if not is_valid:
            click.echo(click.style("Configuration validation failed:", fg='red'))
            for error in errors:
                click.echo(click.style(f"  • {error}", fg='red'))
            return
        project_type = config_data['project']['type']
        project_name = config_data['project']['name']
        # Check if project exists
        output_path = Path(output) / project_name
        if output_path.exists() and not force:
            click.confirm(
                f"Project '{project_name}' already exists. Overwrite?",
                abort=True
            )
        # Select appropriate generator
        if project_type == 'microservice':
            generator = MicroserviceGenerator(config_data, output)
        else:
            raise ValueError(f"Unknown project type: {project_type}")
        # Generate code
        click.echo(f"Generating {project_type} project '{project_name}'...")
        with click.progressbar(length=100, label='Generating project') as bar:
            generator.generate()
            bar.update(100)
        click.echo(click.style(f"\n✓ Project generated successfully!", fg='green', bold=True))
        click.echo(f"\nGenerated structure:")
        click.echo(f"  {output_path}/")
        click.echo(f"  ├── main.py")
        click.echo(f"  ├── requirements.txt")
        click.echo(f"  ├── Dockerfile")
        click.echo(f"  ├── config/")
        click.echo(f"  ├── app/")
        click.echo(f"  └── tests/")
        click.echo(f"\nNext steps:")
        click.echo(f"  cd {output_path}")
        click.echo(f"  pip install -r requirements.txt")
        click.echo(f"  python main.py")
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))
        raise

@cli.command()
@click.argument('config', type=click.Path(exists=True))
def validate(config):
    """Validate a configuration file"""
    try:
        click.echo(f"Validating {config}...")
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        validator = ConfigValidator()
        is_valid, errors = validator.validate(config_data)
        if is_valid:
            click.echo(click.style("✓ Configuration is valid", fg='green', bold=True))
            # Show summary
            project_type = config_data.get('project', {}).get('type', 'unknown')
            click.echo(f"\nProject Type: {project_type}")
            if project_type == 'microservice':
                endpoints = config_data.get('endpoints', [])
                click.echo(f"Endpoints: {len(endpoints)}")
                modules = config_data.get('modules', {})
                enabled_modules = [k for k, v in modules.items()
                                   if isinstance(v, dict) and v.get('enabled')]
                click.echo(f"Enabled Modules: {', '.join(enabled_modules)}")
        else:
            click.echo(click.style("✗ Configuration has errors:", fg='red', bold=True))
            for error in errors:
                click.echo(click.style(f"  • {error}", fg='red'))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
@click.option('--config', '-c', default='nd-config.yaml', type=click.Path(exists=True))
def add_endpoint(config):
    """Add a new endpoint to existing configuration"""
    click.echo(click.style("🔗 Add New Endpoint\n", fg='cyan', bold=True))
    try:
        # Load existing config
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        if config_data.get('project', {}).get('type') != 'microservice':
            click.echo(click.style("Error: Can only add endpoints to microservice projects", fg='red'))
            return
        # Collect endpoint info
        name = click.prompt('Endpoint name')
        path = click.prompt('Path', default=f'/{name}')
        method = click.prompt(
            'HTTP method',
            type=click.Choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
            default='GET'
        )
        description = click.prompt('Description', default=f'{name} endpoint')
        # Input type for non-GET methods
        input_type = 'form'
        if method != 'GET':
            input_type = click.prompt(
                'Input type',
                type=click.Choice(['json', 'form']),
                default='json'
            )
        # Parameters
        params = []
        if click.confirm('Add parameters?', default=True):
            click.echo("Add parameters (empty name to finish):")
            while True:
                param_name = click.prompt('  Parameter name', default='', show_default=False)
                if not param_name:
                    break
                param_type = click.prompt(
                    '  Type',
                    type=click.Choice(['str', 'int', 'float', 'bool', 'list', 'dict']),
                    default='str'
                )
                required = click.confirm('  Required?', default=True)
                param = {
                    'name': param_name,
                    'type': param_type,
                    'required': required
                }
                # Alias
                if click.confirm('  Add alias (for JSON field mapping)?', default=False):
                    param['alias'] = click.prompt('  Alias')
                # Additional validations
                if param_type == 'str':
                    if click.confirm('  Add length constraints?', default=False):
                        param['min_length'] = click.prompt('    Min length', type=int, default=1)
                        param['max_length'] = click.prompt('    Max length', type=int, default=255)
                    if click.confirm('  Add regex pattern?', default=False):
                        param['pattern'] = click.prompt('    Pattern')
                elif param_type in ['int', 'float']:
                    if click.confirm('  Add value constraints?', default=False):
                        param['min_value'] = click.prompt('    Min value', type=float)
                        param['max_value'] = click.prompt('    Max value', type=float)
                if not required and click.confirm('  Set default value?', default=False):
                    param['default'] = click.prompt('  Default value')
                params.append(param)
                click.echo()
        # Caching
        enable_cache = click.confirm('Enable caching?', default=False)
        cache_config = {'enabled': enable_cache}
        if enable_cache:
            cache_config['ttl'] = click.prompt('Cache TTL (seconds)', type=int, default=300)
        # Build endpoint
        endpoint = {
            'name': name,
            'path': path,
            'method': method,
            'description': description,
            'cache': cache_config
        }
        if method != 'GET':
            endpoint['input_type'] = input_type
        if params:
            endpoint['params'] = params
        else:
            endpoint['params'] = []
        # Add to config
        if 'endpoints' not in config_data:
            config_data['endpoints'] = []
        config_data['endpoints'].append(endpoint)
        # Save
        with open(config, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, indent=2)
        click.echo(click.style(f"\n✓ Added endpoint '{name}' to {config}", fg='green', bold=True))
        click.echo(f"\nEndpoint details:")
        click.echo(f"  {method:6} {path}")
        if params:
            click.echo(f"  Parameters: {len(params)}")
        click.echo(f"\nRun 'nd-sdk generate -c {config}' to regenerate project")
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
@click.option('--config', '-c', default='nd-config.yaml', type=click.Path(exists=True))
def preview(config):
    """Preview what will be generated without creating files"""
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        project_name = config_data.get('project', {}).get('name', 'unknown')
        project_type = config_data.get('project', {}).get('type', 'unknown')
        click.echo(click.style(f"Preview: {project_name}\n", fg='cyan', bold=True))
        click.echo(f"Type: {project_type}")
        click.echo(f"Version: {config_data.get('project', {}).get('version', '1.0.0')}")
        # File structure
        click.echo(click.style("\n📁 Project Structure:", fg='yellow', bold=True))
        click.echo(f"{project_name}/")
        click.echo("├── main.py")
        click.echo("├── requirements.txt")
        click.echo("├── Dockerfile")
        click.echo("├── README.md")
        click.echo("├── .gitignore")
        click.echo("├── config/")
        click.echo("│   └── config.yaml")
        click.echo("├── app/")
        click.echo("│   ├── __init__.py")
        click.echo("│   ├── config.py")
        click.echo("│   ├── dependencies.py")
        if project_type == 'microservice':
            endpoints = config_data.get('endpoints', [])
            click.echo("│   ├── models/")
            for endpoint in endpoints:
                click.echo(f"│   │   ├── {endpoint['name']}.py")
            click.echo("│   ├── endpoints/")
            for endpoint in endpoints:
                click.echo(f"│   │   ├── {endpoint['name']}.py")
            click.echo("│   └── services/")
        click.echo("└── tests/")
        click.echo("    ├── unit/")
        click.echo("    └── integration/")
        # Endpoints
        if project_type == 'microservice':
            click.echo(click.style("\n🔗 Endpoints:", fg='yellow', bold=True))
            for endpoint in config_data.get('endpoints', []):
                cached = "📦" if endpoint.get('cache', {}).get('enabled') else "  "
                click.echo(f"{cached} {endpoint['method']:6} {endpoint['path']}")
                if endpoint.get('params'):
                    click.echo(f"         Parameters: {len(endpoint['params'])}")
        # Modules
        click.echo(click.style("\n📦 Enabled Modules:", fg='yellow', bold=True))
        modules = config_data.get('modules', {})
        for module, config_val in modules.items():
            if isinstance(config_val, dict) and config_val.get('enabled'):
                click.echo(f"  ✓ {module}")
            elif module == 'web_framework':
                click.echo(f"  ✓ {module}: {config_val}")
        # Dependencies
        click.echo(click.style("\n📚 Dependencies:", fg='yellow', bold=True))
        click.echo("  • nd-sdk (latest)")
        for pkg in config_data.get('python', {}).get('packages', []):
            click.echo(f"  • {pkg}")
        click.echo(click.style(f"\nRun 'nd-sdk generate -c {config}' to create this project", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
def templates():
    """Browse and use predefined templates"""
    templates_list = [
        {
            'name': 'rest-api-basic',
            'description': 'Simple REST API with CRUD operations',
            'type': 'microservice',
            'features': ['Health check', 'Sample CRUD endpoints', 'Basic logging']
        },
        {
            'name': 'rest-api-full',
            'description': 'Full-featured REST API with auth, caching, storage',
            'type': 'microservice',
            'features': ['Observability', 'Redis caching', 'S3 storage', 'Exception handling']
        },
        {
            'name': 'rest-api-minimal',
            'description': 'Minimal REST API for quick prototyping',
            'type': 'microservice',
            'features': ['Health check only', 'No caching', 'Basic setup']
        },
        {
            'name': 'etl-pipeline',
            'description': 'ETL batch job with S3 integration',
            'type': 'batch-job',
            'features': ['Extract-Transform-Load steps', 'S3 integration', 'Scheduled execution']
        },
        {
            'name': 'event-processor',
            'description': 'Event-driven worker with queue',
            'type': 'worker',
            'features': ['RabbitMQ integration', 'Retry logic', 'Task management']
        }
    ]
    click.echo(click.style("📚 Available Templates\n", fg='cyan', bold=True))
    for i, template in enumerate(templates_list, 1):
        click.echo(click.style(f"{i}. {template['name']}", fg='yellow', bold=True))
        click.echo(f"   {template['description']}")
        click.echo(f"   Type: {template['type']}")
        click.echo(f"   Features: {', '.join(template['features'])}")
        click.echo()
    if click.confirm('Use a template?', default=True):
        choice = click.prompt('Select template', type=click.IntRange(1, len(templates_list)))
        selected = templates_list[choice - 1]
        output_file = click.prompt('Output file', default='nd-config.yaml')
        # Generate config based on template
        template_configs = {
            'rest-api-basic': MICROSERVICE_TEMPLATE,
            'rest-api-full': MICROSERVICE_TEMPLATE,
            'rest-api-minimal': MICROSERVICE_MINIMAL_TEMPLATE,
            'etl-pipeline': BATCH_JOB_TEMPLATE,
            'event-processor': WORKER_TEMPLATE
        }
        with open(output_file, 'w') as f:
            f.write(template_configs.get(selected['name'], MICROSERVICE_TEMPLATE).strip())
        click.echo(click.style(f"\n✓ Created {output_file} from template '{selected['name']}'", fg='green', bold=True))
        click.echo(f"\nNext steps:")
        click.echo(f"  1. Edit {output_file} to customize")
        click.echo(f"  2. nd-sdk generate -c {output_file}")

@cli.command()
@click.argument('config', type=click.Path(exists=True))
def lint(config):
    """Validate and suggest improvements for configuration"""
    try:
        click.echo(f"Analyzing {config}...\n")
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        validator = ConfigValidator()
        is_valid, errors = validator.validate(config_data)
        # Errors
        if errors:
            click.echo(click.style("❌ Errors:", fg='red', bold=True))
            for error in errors:
                click.echo(click.style(f"  • {error}", fg='red'))
            click.echo()
        else:
            click.echo(click.style("✓ No validation errors", fg='green'))
        # Warnings & Suggestions
        suggestions = []
        modules = config_data.get('modules', {})
        # Check observability
        if not modules.get('observability', {}).get('enabled'):
            suggestions.append("Consider enabling observability for better debugging in production")
        # Check caching for GET endpoints
        if config_data.get('project', {}).get('type') == 'microservice':
            endpoints = config_data.get('endpoints', [])
            get_endpoints = [e for e in endpoints if e.get('method') == 'GET']
            cached_endpoints = [e for e in get_endpoints if e.get('cache', {}).get('enabled')]
            if get_endpoints and not cached_endpoints:
                suggestions.append("No GET endpoints have caching enabled. Consider caching for better performance")
        # Check exception handler
        if not modules.get('exception_handler', {}).get('enabled'):
            suggestions.append("Enable exception_handler for consistent error responses")
        # Check storage without providers
        if modules.get('storage', {}).get('enabled'):
            providers = modules.get('storage', {}).get('providers', [])
            if not providers:
                suggestions.append("Storage is enabled but no providers configured")
        # Check Python version
        python_version = config_data.get('python', {}).get('version', '')
        if python_version and python_version < '3.8':
            suggestions.append(f"Python {python_version} is outdated. Consider upgrading to 3.8+")
        if suggestions:
            click.echo(click.style("\n⚠️  Suggestions:", fg='yellow', bold=True))
            for suggestion in suggestions:
                click.echo(click.style(f"  • {suggestion}", fg='yellow'))
        else:
            click.echo(click.style("\n✓ Configuration follows best practices", fg='green'))
        # Best practices tips
        click.echo(click.style("\n💡 Tips:", fg='blue', bold=True))
        click.echo("  • Use environment variables for sensitive configuration")
        click.echo("  • Enable caching for read-heavy endpoints")
        click.echo("  • Keep observability enabled in production")
        click.echo("  • Use semantic versioning for your project")
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))

@cli.command()
@click.argument('config', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['json', 'env', 'summary']), default='summary')
def export(config, format):
    """Export configuration to different formats"""
    try:
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        if format == 'json':
            output = json.dumps(config_data, indent=2)
            click.echo(output)
        elif format == 'env':
            # Generate environment variables from config
            env_vars = []
            project = config_data.get('project', {})
            env_vars.append(f"PROJECT_NAME={project.get('name', '')}")
            env_vars.append(f"PROJECT_TYPE={project.get('type', '')}")
            env_vars.append(f"PROJECT_VERSION={project.get('version', '')}")
            env_vars.append(f"ENVIRONMENT={project.get('environment', 'development')}")
            # Python config
            python = config_data.get('python', {})
            env_vars.append(f"PYTHON_VERSION={python.get('version', '3.8.10')}")
            # Web config
            if config_data.get('web'):
                env_vars.append(f"API_URL_PREFIX={config_data['web'].get('url_prefix', '/api/v1')}")
            # Module configs
            modules = config_data.get('modules', {})
            # Observability
            if modules.get('observability', {}).get('enabled'):
                obs = modules['observability']
                if obs.get('logging', {}).get('enabled'):
                    env_vars.append(f"LOG_LEVEL={obs['logging'].get('level', 'INFO')}")
                if obs.get('tracing', {}).get('enabled'):
                    env_vars.append(f"TRACING_ENABLED=true")
                if obs.get('metrics', {}).get('enabled'):
                    env_vars.append(f"METRICS_ENABLED=true")
            # Caching
            if modules.get('caching', {}).get('enabled'):
                cache = modules['caching']
                env_vars.append(f"CACHE_PROVIDER={cache.get('default_provider', 'inmemory')}")
                if 'redis' in cache.get('providers', {}):
                    redis_config = cache['providers']['redis']
                    env_vars.append(f"REDIS_HOST={redis_config.get('host', 'localhost')}")
                    env_vars.append(f"REDIS_PORT={redis_config.get('port', 6379)}")
            # Storage
            if modules.get('storage', {}).get('enabled'):
                providers = modules['storage'].get('providers', [])
                env_vars.append(f"STORAGE_PROVIDERS={','.join(providers)}")
            # Print env vars
            click.echo("# Environment Variables")
            click.echo("# Generated from: " + config)
            click.echo()
            for var in env_vars:
                click.echo(var)
        elif format == 'summary':
            # Generate summary
            project = config_data.get('project', {})
            click.echo(click.style("Configuration Summary\n", fg='cyan', bold=True))
            click.echo(click.style("Project:", fg='yellow', bold=True))
            click.echo(f"  Name: {project.get('name', 'N/A')}")
            click.echo(f"  Type: {project.get('type', 'N/A')}")
            click.echo(f"  Version: {project.get('version', 'N/A')}")
            click.echo(f"  Environment: {project.get('environment', 'N/A')}")
            # Python
            python = config_data.get('python', {})
            click.echo(click.style("\nPython:", fg='yellow', bold=True))
            click.echo(f"  Version: {python.get('version', 'N/A')}")
            click.echo(f"  Packages: {len(python.get('packages', []))}")
            # Modules
            modules = config_data.get('modules', {})
            if modules:
                click.echo(click.style("\nModules:", fg='yellow', bold=True))
                for module, module_config in modules.items():
                    if isinstance(module_config, dict):
                        enabled = "✓" if module_config.get('enabled') else "✗"
                        click.echo(f"  {enabled} {module}")
                    else:
                        click.echo(f"  ✓ {module}: {module_config}")
            # Endpoints
            if project.get('type') == 'microservice':
                endpoints = config_data.get('endpoints', [])
                if endpoints:
                    click.echo(click.style("\nEndpoints:", fg='yellow', bold=True))
                    for endpoint in endpoints:
                        cached = "📦" if endpoint.get('cache', {}).get('enabled') else "  "
                        params_count = len(endpoint.get('params', []))
                        click.echo(f"  {cached} {endpoint['method']:6} {endpoint['path']} ({params_count} params)")
            # Jobs
            if project.get('type') == 'batch-job':
                jobs = config_data.get('jobs', [])
                if jobs:
                    click.echo(click.style("\nJobs:", fg='yellow', bold=True))
                    for job in jobs:
                        click.echo(f"  • {job.get('name')} - {job.get('schedule', 'N/A')}")
            # Tasks
            if project.get('type') == 'worker':
                tasks = config_data.get('tasks', [])
                if tasks:
                    click.echo(click.style("\nTasks:", fg='yellow', bold=True))
                    for task in tasks:
                        click.echo(f"  • {task.get('name')} - Queue: {task.get('queue', 'N/A')}")
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'))
# Template definitions
MICROSERVICE_TEMPLATE = """
project:
  name: my-microservice
  type: microservice
  description: Sample microservice with ND-SDK
  version: 1.0.0
  environment: development

python:
  version: 3.8.10
  packages:
    - gunicorn==20.1.0
  pre_install_commands:
    - apt-get update

web:
  url_prefix: /api/v1

modules:
  observability:
    enabled: true
    logging:
      enabled: true
      level: INFO
      provider: otel
    tracing:
      enabled: true
      provider: otel
    metrics:
      enabled: true
      provider: otel

  caching:
    enabled: true
    default_provider: redis
    providers:
      redis:
        host: localhost
        port: 6379
      inmemory:
        max_size: 1000

  storage:
    enabled: false
    providers: []

  web_framework: flask

  exception_handler:
    enabled: true
    include_traceback: true

endpoints:
  - name: health_check
    path: /health
    method: GET
    description: Health check endpoint
    params: []
    cache:
      enabled: false

  - name: sample_endpoint
    path: /sample
    method: GET
    description: Sample GET endpoint
    params:
      - name: message
        type: str
        required: true
        alias: message
        min_length: 1
        max_length: 500
    cache:
      enabled: false
"""
MICROSERVICE_MINIMAL_TEMPLATE = """
project:
  name: minimal-api
  type: microservice
  description: Minimal REST API
  version: 1.0.0
  environment: development

python:
  version: 3.8.10
  packages:
    - gunicorn==20.1.0

web:
  url_prefix: /api/v1

modules:
  web_framework: flask
  exception_handler:
    enabled: true

endpoints:
  - name: health_check
    path: /health
    method: GET
    description: Health check
    params: []
    cache:
      enabled: false
"""
BATCH_JOB_TEMPLATE = """
project:
  name: etl-pipeline
  type: batch-job
  description: ETL batch job
  version: 1.0.0
  environment: development

python:
  version: 3.8.10
  packages:
    - pandas==1.3.0

modules:
  observability:
    enabled: true
    logging:
      enabled: true
      level: INFO

  storage:
    enabled: true
    providers:
      - s3

jobs:
  - name: data_processor
    schedule: "0 0 * * *"
    description: Process daily data
    steps:
      - name: extract
        type: extract
      - name: transform
        type: transform
      - name: load
        type: load
"""
WORKER_TEMPLATE = """
project:
  name: event-worker
  type: worker
  description: Event-driven worker
  version: 1.0.0
  environment: development

python:
  version: 3.8.10
  packages:
    - pika==1.2.0

modules:
  observability:
    enabled: true

  queue:
    enabled: true
    provider: rabbitmq
    host: localhost
    port: 5672

tasks:
  - name: process_email
    queue: emails
    retry: 3

  - name: generate_report
    queue: reports
    retry: 5
"""
if __name__ == '__main__':
    cli()