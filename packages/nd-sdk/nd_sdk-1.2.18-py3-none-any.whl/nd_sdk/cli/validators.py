class ConfigValidator:
    """Validates configuration files"""

    REQUIRED_FIELDS = {
        'project': ['name', 'type'],
        'modules': [],
    }

    VALID_PROJECT_TYPES = ['microservice', 'batch-job', 'worker']
    VALID_WEB_FRAMEWORKS = ['fastapi', 'flask']
    VALID_HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
    VALID_PARAM_TYPES = ['str', 'int', 'float', 'bool', 'list', 'dict']

    def validate(self, config):
        """Validate configuration and return (is_valid, errors)"""
        errors = []

        # Check required sections
        if 'project' not in config:
            errors.append("Missing 'project' section")
            return False, errors

        # Validate project fields
        for field in self.REQUIRED_FIELDS['project']:
            if field not in config['project']:
                errors.append(f"Missing required field: project.{field}")

        # Validate project type
        project_type = config['project'].get('type')
        if project_type and project_type not in self.VALID_PROJECT_TYPES:
            errors.append(f"Invalid project type: {project_type}")

        # Validate modules
        if 'modules' in config:
            module_errors = self._validate_modules(config['modules'])
            errors.extend(module_errors)

        # Validate endpoints for microservice
        if project_type == 'microservice' and 'endpoints' in config:
            endpoint_errors = self._validate_endpoints(config['endpoints'])
            errors.extend(endpoint_errors)

        return len(errors) == 0, errors

    def _validate_modules(self, modules):
        """Validate modules configuration"""
        errors = []

        web_framework = modules.get('web_framework')
        if web_framework and web_framework not in self.VALID_WEB_FRAMEWORKS:
            errors.append(f"Invalid web framework: {web_framework}")

        return errors

    def _validate_endpoints(self, endpoints):
        """Validate endpoints configuration"""
        errors = []

        for i, endpoint in enumerate(endpoints):
            # Check required fields
            if 'name' not in endpoint:
                errors.append(f"Endpoint {i}: missing 'name'")
            if 'path' not in endpoint:
                errors.append(f"Endpoint {i}: missing 'path'")
            if 'method' not in endpoint:
                errors.append(f"Endpoint {i}: missing 'method'")

            # Validate method
            method = endpoint.get('method', '').upper()
            if method and method not in self.VALID_HTTP_METHODS:
                errors.append(f"Endpoint {endpoint.get('name')}: invalid method {method}")

            # Validate parameters
            if 'params' in endpoint:
                param_errors = self._validate_params(endpoint['params'], endpoint.get('name'))
                errors.extend(param_errors)

        return errors

    def _validate_params(self, params, endpoint_name):
        """Validate endpoint parameters"""
        errors = []

        for param in params:
            if 'name' not in param:
                errors.append(f"Endpoint {endpoint_name}: parameter missing 'name'")
            if 'type' not in param:
                errors.append(f"Endpoint {endpoint_name}: parameter missing 'type'")

            param_type = param.get('type')
            if param_type and param_type not in self.VALID_PARAM_TYPES:
                errors.append(
                    f"Endpoint {endpoint_name}: invalid parameter type '{param_type}'"
                )

        return errors
