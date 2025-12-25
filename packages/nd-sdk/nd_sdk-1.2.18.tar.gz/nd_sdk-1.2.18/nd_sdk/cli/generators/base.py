from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    """Base class for all code generators"""

    def __init__(self, config, output_dir):
        self.config = config
        self.output_dir = Path(output_dir)
        self.project_name = config['project']['name']
        self.project_dir = self.output_dir / self.project_name

        # Setup Jinja2 environment
        self.env = Environment(
            loader=PackageLoader('nd_sdk', 'cli/templates'),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self.env.filters['snake_case'] = self._snake_case
        self.env.filters['camel_case'] = self._camel_case

    @abstractmethod
    def generate(self):
        """Generate the project structure"""
        pass

    def _snake_case(self, text):
        """Convert text to snake_case"""
        import re
        text = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)
        return text.lower().replace('-', '_').replace(' ', '_')

    def _camel_case(self, text):
        """Convert text to CamelCase"""
        words = text.replace('-', ' ').replace('_', ' ').split()
        return ''.join(word.capitalize() for word in words)

    def _write_file(self, filepath, content):
        """Write content to file with UTF-8 encoding"""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding='utf-8')

    def _render_template(self, template_name, **kwargs):
        """Render a Jinja2 template"""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)


if __name__ == '__main__':
    cli()