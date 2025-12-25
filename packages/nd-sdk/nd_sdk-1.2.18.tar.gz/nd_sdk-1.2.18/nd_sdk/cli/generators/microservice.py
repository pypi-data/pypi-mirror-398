# from .cli.generators.base import BaseGenerator
from pathlib import Path
from .base import BaseGenerator


class MicroserviceGenerator(BaseGenerator):
    """Generator for microservice projects"""

    def generate(self):
        """Generate complete microservice project structure"""

        # Create project directory
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Generate files
        self._generate_structure()
        self._generate_main()
        self._generate_endpoints()
        self._generate_dependencies()
        self._generate_services()
        self._generate_settings()
        self._generate_requirements()
        self._generate_dockerfile()
        self._generate_readme()
        self._generate_gitignore()
        self._generate_models()
        self._generate_config()

        print(f"\n✓ Project structure created at: {self.project_dir}")
        self._print_structure()

    def _generate_structure(self):
        """Create directory structure"""
        dirs = [
            'app',
            'app/endpoints',
            'app/models',
            'app/services',
            'app/utils',
            'tests',
            'tests/unit',
            'tests/integration',
            'app/core'
        ]

        for dir_path in dirs:
            (self.project_dir / dir_path).mkdir(parents=True, exist_ok=True)
            (self.project_dir / dir_path / '__init__.py').touch()

    def _generate_main(self):
        """Generate main.py"""
        content = self._render_template(
            'microservice/main.py.j2',
            config=self.config,
            project_name=self.project_name,
            web_framework=self.config.get('modules', {}).get('web_framework', 'fastapi')
        )
        self._write_file(self.project_dir / 'main.py', content)

    def _generate_models(self):
        """Generate Pydantic models"""
        # Generate models for each endpoint
        for endpoint in self.config.get('endpoints', []):
            # if not endpoint.get('params'):
            #     continue

            content = self._render_template(
                'microservice/model.py.j2',
                endpoint=endpoint,
                config=self.config,
            )

            model_file = self.project_dir / 'app' / 'models' / f"{endpoint['name']}.py"
            self._write_file(model_file, content)

        # Generate __init__.py with all models
        all_models_content = self._render_template(
            'microservice/models_init.py.j2',
            endpoints=self.config.get('endpoints', []),
            config=self.config,
        )
        self._write_file(
            self.project_dir / 'app' / 'models' / '__init__.py',
            all_models_content
        )

    def _generate_endpoints(self):
        """Generate endpoint files"""
        for endpoint in self.config.get('endpoints', []):
            content = self._render_template(
                'microservice/endpoint.py.j2',
                endpoint=endpoint,
                web_framework=self.config['modules'].get('web_framework', 'fastapi'),
                web=self.config['web'],
                config=self.config,
            )

            endpoint_file = self.project_dir / 'app' / 'endpoints' / f"{endpoint['name']}.py"
            self._write_file(endpoint_file, content)

        # Generate router __init__.py
        router_content = self._render_template(
            'microservice/endpoints_init.py.j2',
            endpoints=self.config.get('endpoints', []),
            config=self.config,
            web_framework=self.config['modules'].get('web_framework', 'fastapi'),
        )
        self._write_file(
            self.project_dir / 'app' / 'endpoints' / '__init__.py',
            router_content
        )

    def _generate_dependencies(self):
        """Generate dependencies (framework specific)"""
        content = self._render_template(
            'microservice/dependencies.py.j2',
            config=self.config,
            web_framework=self.config.get('modules', {}).get('web_framework', 'fastapi')
        )
        self._write_file(self.project_dir / 'app' / 'dependencies.py', content)

    def _generate_settings(self):
        """Generate settings.py for configuration management"""
        content = self._render_template(
            'microservice/settings.py.j2',
            config=self.config,
        )
        self._write_file(self.project_dir / 'app' / 'settings.py', content)

    def _generate_core_business_logic(self):
        """Generate core business logic files"""
        for endpoint in self.config.get('endpoints', []):
            content = self._render_template(
                'microservice/business_logic.py.j2',
                endpoint=endpoint,
                config=self.config,
            )
            self._write_file(
                self.project_dir / 'app' / 'services' / f"{endpoint['name']}_business_logic.py",
                content
            )

    def _generate_config(self):
        """Generate config.yaml and config loader"""
        # Generate config.yaml
        config_content = self._render_template(
            'microservice/config.yaml.j2',
            config=self.config,  # Pass config here
        )
        self._write_file(self.project_dir / 'config' / 'config.yaml', config_content)

        # Generate config.py loader - ADD config parameter here!
        loader_content = self._render_template(
            'microservice/config_loader.py.j2',
            config=self.config  # ← THIS WAS MISSING!
        )
        self._write_file(self.project_dir / 'app' / 'config.py', loader_content)

    def _generate_services(self):
        # base service
        base_content = self._render_template(
            'microservice/service_base.py.j2'
        )
        self._write_file(
            self.project_dir / 'app' / 'services' / 'base.py',
            base_content
        )

        # per-endpoint services
        for endpoint in self.config.get('endpoints', []):
            content = self._render_template(
                'microservice/service.py.j2',
                endpoint=endpoint
            )
            self._write_file(
                self.project_dir / 'app' / 'services' / f"{endpoint['name']}_service.py",
                content
            )

    def _generate_requirements(self):
        """Generate requirements.txt"""
        requirements = ['nd-sdk']

        # Web framework
        web_framework = self.config['modules'].get('web_framework', 'fastapi')
        if web_framework == 'fastapi':
            requirements.extend(['fastapi', 'uvicorn[standard]', 'pydantic>=2.0.0'])
        elif web_framework == 'flask':
            requirements.append('flask')

        # Modules
        modules = self.config.get('modules', {})

        if modules.get('caching', {}).get('enabled'):
            requirements.append('redis>=4.0.0')

        if modules.get('storage', {}).get('enabled'):
            requirements.append('boto3')

        if modules.get('observability', {}).get('enabled'):
            requirements.extend([
                'opentelemetry-api',
                'opentelemetry-sdk',
                'prometheus-client',
            ])

        # Additional common dependencies
        requirements.extend([
            'python-dotenv',
            'pyyaml',
        ])

        content = '\n'.join(sorted(set(requirements)))
        self._write_file(self.project_dir / 'requirements.txt', content)

    def _generate_dockerfile(self):
        """Generate Dockerfile"""
        content = self._render_template(
            'microservice/Dockerfile.j2',
            project_name=self.project_name,
            config=self.config,
        )
        self._write_file(self.project_dir / 'Dockerfile', content)

    def _generate_readme(self):
        """Generate README.md"""
        content = self._render_template(
            'microservice/README.md.j2',
            config=self.config,
            project_name=self.project_name,
        )
        self._write_file(self.project_dir / 'README.md', content)

    def _generate_gitignore(self):
        """Generate .gitignore"""
        gitignore_content = """""".strip()
        self._write_file(self.project_dir / '.gitignore', gitignore_content)

    def _print_structure(self):
        """Print generated project structure"""
        print(f"\nGenerated structure:")
        print(f"{self.project_name}/")
        print("├── main.py")
        print("├── requirements.txt")
        print("├── Dockerfile")
        print("├── README.md")
        print("├── .gitignore")
        print("├── config/")
        print("│   └── config.yaml")
        print("├── app/")
        print("│   ├── __init__.py")
        print("│   ├── config.py")
        print("│   ├── dependencies.py")
        print("│   ├── models/")
        for endpoint in self.config.get('endpoints', []):
            print(f"│   │   ├── {endpoint['name']}.py")
        print("│   ├── endpoints/")
        for endpoint in self.config.get('endpoints', []):
            print(f"│   │   ├── {endpoint['name']}.py")
        print("│   └── services/")
        print("└── tests/")
        print("    ├── unit/")
        print("    └── integration/")
