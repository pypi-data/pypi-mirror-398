"""
JSON Generator Module
Generates JSON documentation for APIs
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

from .parser import AppAPIInfo, EndpointInfo, FieldInfo


class JSONGenerator:
    """
    Generates JSON documentation for APIs (compatible with OpenAPI/Swagger format)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize JSON generator
        
        Args:
            config: Configuration dictionary with title, version, etc.
        """
        self.config = config or {}
        self.title = self.config.get('TITLE', 'API Documentation')
        self.version = self.config.get('VERSION', '1.0.0')
        self.description = self.config.get('DESCRIPTION', 'Complete API Reference')
        
    def generate(self, apps: List[AppAPIInfo], output_path: str) -> str:
        """
        Generate JSON documentation (OpenAPI 3.0 format)
        
        Args:
            apps: List of AppAPIInfo objects with parsed API data
            output_path: Path to save the JSON file
            
        Returns:
            Path to the generated JSON file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        openapi_doc = self._generate_openapi(apps)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(openapi_doc, f, indent=2, ensure_ascii=False)
        
        return os.path.abspath(output_path)
    
    def _generate_openapi(self, apps: List[AppAPIInfo]) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 compliant documentation"""
        
        doc = {
            'openapi': '3.0.3',
            'info': {
                'title': self.title,
                'version': self.version,
                'description': self.description,
                'x-generated-at': datetime.now().isoformat(),
                'x-generator': 'Django REST API Documentation Generator',
            },
            'servers': [
                {
                    'url': '/',
                    'description': 'API Server'
                }
            ],
            'tags': [],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {}
            }
        }
        
        # Add tags from apps
        for app in apps:
            doc['tags'].append({
                'name': app.app_name,
                'description': app.description or f'API endpoints for {app.app_label}'
            })
        
        # Add paths
        security_schemes_added = set()
        
        for app in apps:
            for endpoint in app.endpoints:
                path = endpoint.url
                
                if path not in doc['paths']:
                    doc['paths'][path] = {}
                
                for method in endpoint.methods:
                    method_lower = method.lower()
                    
                    operation = {
                        'tags': [app.app_name],
                        'summary': endpoint.name,
                        'description': endpoint.description,
                        'operationId': f"{app.app_name}_{endpoint.name}_{method_lower}".replace(' ', '_'),
                        'responses': self._generate_responses(endpoint),
                    }
                    
                    # Add parameters (path + query)
                    parameters = self._generate_parameters(endpoint)
                    if parameters:
                        operation['parameters'] = parameters
                    
                    # Add request body for methods that support it
                    if method_lower in ['post', 'put', 'patch'] and endpoint.request_fields:
                        operation['requestBody'] = self._generate_request_body(endpoint)
                    
                    # Add security
                    if endpoint.authentication and 'None (Public)' not in endpoint.authentication:
                        security = []
                        for auth in endpoint.authentication:
                            auth_key = self._sanitize_key(auth)
                            security.append({auth_key: []})
                            
                            if auth_key not in security_schemes_added:
                                doc['components']['securitySchemes'][auth_key] = self._get_security_scheme(auth)
                                security_schemes_added.add(auth_key)
                        
                        operation['security'] = security
                    
                    # Add deprecated flag if applicable
                    if endpoint.deprecated:
                        operation['deprecated'] = True
                    
                    doc['paths'][path][method_lower] = operation
        
        return doc
    
    def _generate_parameters(self, endpoint: EndpointInfo) -> List[Dict]:
        """Generate OpenAPI parameters from endpoint"""
        parameters = []
        
        # Path parameters
        for param in endpoint.path_params:
            parameters.append({
                'name': param,
                'in': 'path',
                'required': True,
                'schema': {'type': 'string'},
                'description': f'Path parameter: {param}'
            })
        
        # Query parameters
        for field in endpoint.query_params:
            param = {
                'name': field.name,
                'in': 'query',
                'required': field.required,
                'schema': self._field_to_schema(field),
            }
            if field.help_text:
                param['description'] = field.help_text
            parameters.append(param)
        
        return parameters
    
    def _generate_request_body(self, endpoint: EndpointInfo) -> Dict:
        """Generate OpenAPI request body"""
        properties = {}
        required = []
        
        for field in endpoint.request_fields:
            if field.read_only:
                continue
            
            properties[field.name] = self._field_to_schema(field)
            
            if field.required:
                required.append(field.name)
        
        schema = {
            'type': 'object',
            'properties': properties
        }
        
        if required:
            schema['required'] = required
        
        return {
            'required': True,
            'content': {
                'application/json': {
                    'schema': schema,
                    'example': self._create_example(endpoint.request_fields, is_request=True)
                }
            }
        }
    
    def _generate_responses(self, endpoint: EndpointInfo) -> Dict:
        """Generate OpenAPI responses"""
        responses = {}
        
        # Success response
        if endpoint.response_fields:
            properties = {}
            for field in endpoint.response_fields:
                if field.write_only:
                    continue
                properties[field.name] = self._field_to_schema(field)
            
            responses['200'] = {
                'description': 'Successful response',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': properties
                        },
                        'example': self._create_example(endpoint.response_fields, is_request=False)
                    }
                }
            }
        else:
            responses['200'] = {
                'description': 'Successful response'
            }
        
        # Common error responses
        responses['400'] = {
            'description': 'Bad Request',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'detail': {'type': 'string'}
                        }
                    }
                }
            }
        }
        
        responses['401'] = {
            'description': 'Unauthorized',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'detail': {'type': 'string'}
                        }
                    }
                }
            }
        }
        
        responses['404'] = {
            'description': 'Not Found',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'detail': {'type': 'string'}
                        }
                    }
                }
            }
        }
        
        return responses
    
    def _field_to_schema(self, field: FieldInfo) -> Dict:
        """Convert FieldInfo to OpenAPI schema"""
        type_mapping = {
            'string': {'type': 'string'},
            'email': {'type': 'string', 'format': 'email'},
            'url': {'type': 'string', 'format': 'uri'},
            'integer': {'type': 'integer'},
            'float': {'type': 'number', 'format': 'float'},
            'decimal': {'type': 'string', 'format': 'decimal'},
            'boolean': {'type': 'boolean'},
            'date': {'type': 'string', 'format': 'date'},
            'datetime': {'type': 'string', 'format': 'date-time'},
            'time': {'type': 'string', 'format': 'time'},
            'uuid': {'type': 'string', 'format': 'uuid'},
            'file': {'type': 'string', 'format': 'binary'},
            'image': {'type': 'string', 'format': 'binary'},
            'array': {'type': 'array', 'items': {}},
            'object': {'type': 'object'},
            'json': {'type': 'object'},
            'integer (pk)': {'type': 'integer'},
            'string (slug)': {'type': 'string'},
        }
        
        base_type = field.field_type.lower()
        schema = type_mapping.get(base_type, {'type': 'string'}).copy()
        
        # Add constraints
        if field.max_length:
            schema['maxLength'] = field.max_length
        if field.min_length:
            schema['minLength'] = field.min_length
        if field.max_value is not None:
            schema['maximum'] = field.max_value
        if field.min_value is not None:
            schema['minimum'] = field.min_value
        if field.choices:
            schema['enum'] = field.choices
        if field.help_text:
            schema['description'] = field.help_text
        if field.default is not None and str(field.default) != 'empty':
            # Only include JSON-serializable defaults
            try:
                default_val = field.default
                # Check if it's a simple serializable type
                if isinstance(default_val, (str, int, float, bool, list, dict, type(None))):
                    json.dumps(default_val)  # Test if serializable
                    schema['default'] = default_val
            except (TypeError, ValueError):
                pass  # Skip non-serializable defaults
        
        # Handle nested fields
        if field.child_fields:
            if schema.get('type') == 'array':
                child_properties = {}
                for child in field.child_fields:
                    child_properties[child.name] = self._field_to_schema(child)
                schema['items'] = {
                    'type': 'object',
                    'properties': child_properties
                }
            else:
                child_properties = {}
                for child in field.child_fields:
                    child_properties[child.name] = self._field_to_schema(child)
                schema['properties'] = child_properties
        
        return schema
    
    def _create_example(self, fields: List[FieldInfo], is_request: bool = True) -> Dict:
        """Create example object from fields"""
        example = {}
        
        for field in fields:
            if is_request and field.read_only:
                continue
            if not is_request and field.write_only:
                continue
            
            example[field.name] = self._get_example_value(field)
        
        return example
    
    def _get_example_value(self, field: FieldInfo) -> Any:
        """Get example value for a field"""
        if field.default is not None and str(field.default) != 'empty':
            # Check if the default is JSON serializable
            try:
                default_val = field.default
                if isinstance(default_val, (str, int, float, bool, list, dict, type(None))):
                    return default_val
            except:
                pass
        
        if field.choices:
            return field.choices[0] if field.choices else None
        
        type_examples = {
            'string': 'example_string',
            'email': 'user@example.com',
            'url': 'https://example.com',
            'integer': 1,
            'float': 1.5,
            'decimal': '10.00',
            'boolean': True,
            'date': '2024-01-15',
            'datetime': '2024-01-15T10:30:00Z',
            'time': '10:30:00',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
            'file': 'example.pdf',
            'image': 'example.jpg',
            'array': [],
            'object': {},
            'json': {},
            'integer (pk)': 1,
            'string (slug)': 'example-slug',
        }
        
        base_type = field.field_type.lower()
        
        if base_type in type_examples:
            return type_examples[base_type]
        
        if 'integer' in base_type or 'pk' in base_type:
            return 1
        if 'string' in base_type:
            return f'example_{field.name}'
        
        return None
    
    def _get_security_scheme(self, auth_class_name: str) -> Dict:
        """Get OpenAPI security scheme based on authentication class"""
        auth_lower = auth_class_name.lower()
        
        if 'jwt' in auth_lower or 'token' in auth_lower:
            return {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT'
            }
        elif 'basic' in auth_lower:
            return {
                'type': 'http',
                'scheme': 'basic'
            }
        elif 'session' in auth_lower:
            return {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'sessionid'
            }
        else:
            return {
                'type': 'http',
                'scheme': 'bearer'
            }
    
    def _sanitize_key(self, key: str) -> str:
        """Sanitize a string to be used as a key"""
        import re
        key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
        return key.lower()
