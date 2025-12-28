"""
API Parser Module
Extracts API information from Django REST Framework applications
"""

import inspect
import re
from typing import Dict, List, Any, Optional, Type, Tuple
from dataclasses import dataclass, field
from django.urls import URLResolver, URLPattern, get_resolver
from django.apps import apps
from django.conf import settings

try:
    from rest_framework.views import APIView
    from rest_framework.viewsets import ViewSet, ModelViewSet
    from rest_framework.serializers import Serializer, ModelSerializer
    from rest_framework.permissions import BasePermission
    from rest_framework.authentication import BaseAuthentication
    from rest_framework.decorators import action
    HAS_DRF = True
except ImportError:
    HAS_DRF = False


@dataclass
class FieldInfo:
    """Information about a serializer field"""
    name: str
    field_type: str
    required: bool = False
    read_only: bool = False
    write_only: bool = False
    help_text: str = ""
    default: Any = None
    choices: List[Any] = field(default_factory=list)
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    max_value: Optional[Any] = None
    min_value: Optional[Any] = None
    child_fields: List['FieldInfo'] = field(default_factory=list)


@dataclass
class EndpointInfo:
    """Information about an API endpoint"""
    url: str
    name: str
    methods: List[str]
    view_class: str
    view_name: str
    description: str = ""
    authentication: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    request_fields: List[FieldInfo] = field(default_factory=list)
    response_fields: List[FieldInfo] = field(default_factory=list)
    query_params: List[FieldInfo] = field(default_factory=list)
    path_params: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False
    custom_responses: Dict[int, Dict] = field(default_factory=dict)


@dataclass
class AppAPIInfo:
    """Complete API information for an app"""
    app_name: str
    app_label: str
    description: str
    version: str
    endpoints: List[EndpointInfo] = field(default_factory=list)


class APIParser:
    """
    Parser to extract API information from Django REST Framework apps
    """
    
    # HTTP methods to check for views
    HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    # Mapping of DRF action names to HTTP methods
    ACTION_METHOD_MAP = {
        'list': 'GET',
        'create': 'POST',
        'retrieve': 'GET',
        'update': 'PUT',
        'partial_update': 'PATCH',
        'destroy': 'DELETE',
    }
    
    def __init__(self, app_names: List[str] = None):
        """
        Initialize the parser
        
        Args:
            app_names: List of app names to parse. If None, parse all installed apps.
        """
        if not HAS_DRF:
            raise ImportError(
                "Django REST Framework is required. "
                "Install it with: pip install djangorestframework"
            )
        
        self.app_names = app_names or []
        self.parsed_apps: List[AppAPIInfo] = []
        
    def parse_all(self) -> List[AppAPIInfo]:
        """
        Parse all specified apps and return their API information
        
        Returns:
            List of AppAPIInfo objects containing API documentation
        """
        resolver = get_resolver()
        
        if not self.app_names:
            # Get all installed apps
            self.app_names = [
                app.name.split('.')[-1] 
                for app in apps.get_app_configs()
                if not app.name.startswith('django.')
            ]
        
        for app_name in self.app_names:
            try:
                app_info = self._parse_app(app_name, resolver)
                if app_info.endpoints:
                    self.parsed_apps.append(app_info)
            except Exception as e:
                print(f"Warning: Could not parse app '{app_name}': {e}")
                
        return self.parsed_apps
    
    def _parse_app(self, app_name: str, resolver: URLResolver) -> AppAPIInfo:
        """
        Parse a single app and extract its API information
        
        Args:
            app_name: Name of the app to parse
            resolver: Django URL resolver
            
        Returns:
            AppAPIInfo object with all endpoints
        """
        app_config = None
        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            pass
        
        app_info = AppAPIInfo(
            app_name=app_name,
            app_label=app_config.verbose_name if app_config else app_name.title(),
            description=self._get_app_description(app_config) if app_config else "",
            version=getattr(settings, 'API_VERSION', '1.0.0')
        )
        
        # Extract endpoints from URL patterns
        endpoints = self._extract_endpoints(resolver, app_name)
        app_info.endpoints = endpoints
        
        return app_info
    
    def _get_app_description(self, app_config) -> str:
        """Get app description from docstring or config"""
        if hasattr(app_config, 'module'):
            module_doc = getattr(app_config.module, '__doc__', '')
            if module_doc:
                return module_doc.strip()
        return f"API endpoints for {app_config.verbose_name}"
    
    def _extract_endpoints(self, resolver: URLResolver, app_name: str, 
                          prefix: str = '') -> List[EndpointInfo]:
        """
        Extract all endpoints from URL patterns
        
        Args:
            resolver: URL resolver or pattern
            app_name: Name of the app to filter
            prefix: URL prefix for nested patterns
            
        Returns:
            List of EndpointInfo objects
        """
        endpoints = []
        
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLResolver):
                # Recursively process nested URL patterns
                new_prefix = prefix + self._get_pattern_path(pattern)
                endpoints.extend(self._extract_endpoints(pattern, app_name, new_prefix))
            elif isinstance(pattern, URLPattern):
                # Process individual URL pattern
                endpoint = self._process_pattern(pattern, app_name, prefix)
                if endpoint:
                    endpoints.append(endpoint)
                    
        return endpoints
    
    def _get_pattern_path(self, pattern) -> str:
        """Extract path string from URL pattern"""
        if hasattr(pattern, 'pattern'):
            path = str(pattern.pattern)
        else:
            path = str(pattern.regex.pattern if hasattr(pattern, 'regex') else pattern)
        
        # Clean up regex patterns
        path = path.replace('^', '').replace('$', '')
        return path
    
    def _process_pattern(self, pattern: URLPattern, app_name: str, 
                        prefix: str = '') -> Optional[EndpointInfo]:
        """
        Process a single URL pattern and extract endpoint information
        
        Args:
            pattern: URL pattern to process
            app_name: Name of the app to filter
            prefix: URL prefix
            
        Returns:
            EndpointInfo object or None if not relevant
        """
        callback = pattern.callback
        
        if callback is None:
            return None
        
        # Get the view class
        view_class = getattr(callback, 'cls', None)
        if view_class is None:
            view_class = getattr(callback, 'view_class', None)
        if view_class is None and hasattr(callback, '__self__'):
            view_class = type(callback.__self__)
            
        if view_class is None:
            return None
            
        # Check if this is a DRF view
        if not (hasattr(view_class, 'as_view') or 
                issubclass(view_class, APIView) if inspect.isclass(view_class) else False):
            return None
        
        # Check if the view belongs to the specified app
        view_module = getattr(view_class, '__module__', '')
        if app_name not in view_module.split('.'):
            return None
        
        # Build the full URL path
        full_path = '/' + prefix + self._get_pattern_path(pattern)
        full_path = re.sub(r'/+', '/', full_path)  # Remove duplicate slashes
        
        # Extract path parameters
        path_params = re.findall(r'<(?:[\w:]+:)?(\w+)>', full_path)
        
        # Convert path parameter syntax for display
        full_path = re.sub(r'<(?:[\w:]+:)?(\w+)>', r'{\1}', full_path)
        
        # Get HTTP methods supported by this endpoint
        methods = self._get_view_methods(view_class, callback)
        
        if not methods:
            return None
        
        # Extract authentication and permission info
        auth_classes = self._get_auth_classes(view_class)
        perm_classes = self._get_permission_classes(view_class)
        
        # Extract serializer information for request/response
        request_fields, response_fields = self._get_serializer_fields(view_class, callback)
        
        # Get query parameters from filter backends
        query_params = self._get_query_params(view_class)
        
        # Get view description from docstring
        description = self._get_view_description(view_class, callback)
        
        return EndpointInfo(
            url=full_path,
            name=pattern.name or view_class.__name__,
            methods=methods,
            view_class=view_class.__module__ + '.' + view_class.__name__,
            view_name=view_class.__name__,
            description=description,
            authentication=auth_classes,
            permissions=perm_classes,
            request_fields=request_fields,
            response_fields=response_fields,
            query_params=query_params,
            path_params=path_params,
            tags=[app_name],
        )
    
    def _get_view_methods(self, view_class: Type, callback) -> List[str]:
        """
        Get HTTP methods supported by a view
        
        Args:
            view_class: The view class
            callback: The view callback
            
        Returns:
            List of HTTP method names (uppercase)
        """
        methods = []
        
        # Check for standard HTTP methods
        for method in self.HTTP_METHODS:
            if hasattr(view_class, method) and callable(getattr(view_class, method)):
                methods.append(method.upper())
        
        # Check for ViewSet actions
        if hasattr(callback, 'actions'):
            actions = callback.actions
            if isinstance(actions, dict):
                for http_method, action_name in actions.items():
                    methods.append(http_method.upper())
        
        # Remove duplicates while preserving order
        seen = set()
        methods = [m for m in methods if not (m in seen or seen.add(m))]
        
        return methods
    
    def _get_auth_classes(self, view_class: Type) -> List[str]:
        """Extract authentication classes from view"""
        auth_classes = []
        
        if hasattr(view_class, 'authentication_classes'):
            for auth_class in view_class.authentication_classes:
                if inspect.isclass(auth_class):
                    auth_classes.append(auth_class.__name__)
                elif hasattr(auth_class, '__class__'):
                    auth_classes.append(auth_class.__class__.__name__)
        
        return auth_classes if auth_classes else ['None (Public)']
    
    def _get_permission_classes(self, view_class: Type) -> List[str]:
        """Extract permission classes from view"""
        perm_classes = []
        
        if hasattr(view_class, 'permission_classes'):
            for perm_class in view_class.permission_classes:
                if inspect.isclass(perm_class):
                    perm_classes.append(perm_class.__name__)
                elif hasattr(perm_class, '__class__'):
                    perm_classes.append(perm_class.__class__.__name__)
        
        return perm_classes if perm_classes else ['AllowAny']
    
    def _get_serializer_fields(self, view_class: Type, callback=None) -> Tuple[List[FieldInfo], List[FieldInfo]]:
        """
        Extract request and response fields from serializer or docstring
        """
        request_fields = []
        response_fields = []
        
        # Method 1: Docstring Parsing (Highest Priority) ⭐
        # Check if fields are defined in the docstring (Body: {...})
        doc_request_fields, doc_response_fields = self._parse_docstring_params(view_class, callback)
        
        if doc_request_fields:
            request_fields = doc_request_fields
        if doc_response_fields:
            response_fields = doc_response_fields
            
        # If we found fields in docstring, use them as the primary source
        if doc_request_fields or doc_response_fields:
             return request_fields, response_fields

        serializer_class = getattr(view_class, 'serializer_class', None)
        
        if serializer_class is None:
            # Method 2: Aggressive Instantiation
            # Try to instantiate and call get_serializer_class()
            try:
                view_instance = view_class()
                
                # Mock attributes that get_serializer_class might need
                view_instance.request = None
                view_instance.format_kwarg = None
                view_instance.action = 'list' # Default assumption
                
                if hasattr(view_instance, 'get_serializer_class'):
                    serializer_class = view_instance.get_serializer_class()
            except:
                pass

        if serializer_class is None:
            # Method 3: Check for input/request_serializer attributes
            serializer_class = getattr(view_class, 'input_serializer_class', None) or \
                               getattr(view_class, 'request_serializer_class', None)

        if serializer_class is None:
            # Method 4: Source Code Inspection (The "Sherlock Holmes" method)
            # Read the source code of the method (e.g. post, put) and look for "MySerializer("
            serializer_class = self._find_serializer_in_source(view_class)

        if serializer_class is None:
            # Method 5: Manual Parameter Discovery (The "Raw Data" method)
            # If no serializer is found, scan source code for request.data.get('key') usage
            manual_request_fields = self._scan_for_manual_parameters(view_class)
            
            # Use found request fields
            if manual_request_fields:
                request_fields = manual_request_fields
                
            # Scan for manual response fields (looking for dict keys)
            manual_response_fields = self._scan_for_manual_response_fields(view_class)
            if manual_response_fields:
                 response_fields = manual_response_fields
                 
            if request_fields or response_fields:
                return request_fields, response_fields

            return request_fields, response_fields
        
        try:
            # Instantiate the serializer to get fields
            if inspect.isclass(serializer_class) and issubclass(serializer_class, Serializer):
                serializer = serializer_class()
                
                for field_name, field_obj in serializer.fields.items():
                    field_info = self._extract_field_info(field_name, field_obj)
                    
                    # Request fields (writable)
                    if not field_info.read_only:
                        request_fields.append(field_info)
                    
                    # Response fields (readable)
                    if not field_info.write_only:
                        response_fields.append(field_info)
                        
        except Exception as e:
            print(f"Warning: Could not extract serializer fields: {e}")
            
        return request_fields, response_fields
    
    def _parse_docstring_params(self, view_class: Type, callback=None) -> Tuple[List[FieldInfo], List[FieldInfo]]:
        """
        Parse view docstrings for 'Body: {...}' or 'Response: {...}' sections.
        Checks both the view class and the specific method docstring.
        """
        req_fields = []
        res_fields = []
        
        # Combine docstrings from class and method
        docs = []
        if view_class.__doc__:
            docs.append(view_class.__doc__)
        if callback and callback.__doc__:
            docs.append(callback.__doc__)
            
        doc = "\n\n".join(docs).strip()
        if not doc:
            return req_fields, res_fields
            
        try:
            # 1. Parse Request Body
            # Read everything after 'Body:' or 'Request:' until 'Response:' or End
            # This handles nested brackets {} [] correctly by just taking the whole block
            
            # Find start of Body
            body_match = re.search(r'(?:Body|Request)\s*:', doc, re.IGNORECASE)
            if body_match:
                start_idx = body_match.end()
                
                # Find end (Response section or End of doc)
                end_match = re.search(r'(?:Response|Returns)\s*:', doc[start_idx:], re.IGNORECASE)
                if end_match:
                    block = doc[start_idx : start_idx + end_match.start()]
                else:
                    block = doc[start_idx:]
                
                # Extract keys: "key" or 'key' or just key followed by :
                # This is more robust for manual docstring entries
                keys = set(re.findall(r"['\"]?(\w+)['\"]?\s*:", block))
                
                if keys:
                     print(f"  [INFO] Docstring Body Params for {view_class.__name__}: {keys}")
                     
                for key in keys:
                    req_fields.append(FieldInfo(
                        name=key, type='string', required=False, description='From docstring'
                    ))

            # 2. Parse Response Body
            res_match = re.search(r'(?:Response|Returns)\s*:', doc, re.IGNORECASE)
            if res_match:
                block = doc[res_match.end():]
                
                keys = set(re.findall(r"['\"](\w+)['\"]\s*:", block))
                
                if keys:
                     print(f"  [INFO] Docstring Response Params for {view_class.__name__}: {keys}")
                     
                for key in keys:
                    res_fields.append(FieldInfo(
                        name=key, type='string', required=False, description='From docstring'
                    ))
                     
        except Exception as e:
            print(f"  [DEBUG] Docstring parsing error: {e}")
            pass
            
        return req_fields, res_fields

    def _find_serializer_in_source(self, view_class: Type) -> Optional[Type]:
        """
        Scan the view's source code to find usage of Serializers.
        """
        try:
            source = inspect.getsource(view_class)
            matches = re.findall(r'(\w+Serializer)\s*\(', source) # Allow spaces before (
            
            if matches:
                # print(f"  [DEBUG] Found candidate serializers in {view_class.__name__}: {matches}")
                module = inspect.getmodule(view_class)
                for candidate_name in matches:
                    if hasattr(module, candidate_name):
                        candidate_class = getattr(module, candidate_name)
                        if inspect.isclass(candidate_class) and issubclass(candidate_class, Serializer):
                            print(f"  [INFO] Auto-detected Serializer for {view_class.__name__}: {candidate_name}")
                            return candidate_class
        except Exception as e:
            # print(f"  [DEBUG] Error inspecting source for {view_class.__name__}: {e}")
            pass
        return None

    def _scan_for_manual_parameters(self, view_class: Type) -> List[FieldInfo]:
        """
        Scan source code for manual parameter access (request.data.get or request.data[])
        """
        fields = []
        try:
            source = inspect.getsource(view_class)
            
            # Allow flexible spacing: request.data.get ( 'param' )
            
            # Pattern 1: request.data['param'] -> Required
            required_params = set(re.findall(r"request\.data\[\s*['\"](\w+)['\"]\s*\]", source))
            
            # Pattern 2: request.data.get('param') -> Optional
            optional_params = set(re.findall(r"request\.data\.get\(\s*['\"](\w+)['\"]", source))
            
            all_params = required_params.union(optional_params)
            
            if all_params:
                print(f"  [INFO] Auto-detected Manual Params for {view_class.__name__}: {all_params}")
            
            for param in all_params:
                is_required = param in required_params
                fields.append(FieldInfo(
                    name=param,
                    type='string',
                    required=is_required, 
                    description='Auto-detected parameter'
                ))
        except Exception as e:
            print(f"  [DEBUG] Error scanning manual params for {view_class.__name__}: {e}")
            pass
            
        return fields

        return fields

    def _scan_for_manual_response_fields(self, view_class: Type) -> List[FieldInfo]:
        """
        Scan source code for manual response dict construction (heuristic).
        """
        fields = []
        try:
            source = inspect.getsource(view_class)
            # Find usage of dictionary keys: "key": value
            # This is heuristic and might find internal dicts too, but it's better than empty.
            
            # Pattern: "some_key": ... or 'some_key': ...
            keys = set(re.findall(r"['\"](\w+)['\"]\s*:", source))

            # Sort for consistency
            sorted_keys = sorted(list(keys))
            
            if sorted_keys:
                print(f"  [INFO] Auto-detected Response Keys for {view_class.__name__}: {sorted_keys}")
            
            for key in sorted_keys:
                # Simple filter to avoid too much noise
                if len(key) > 1 and not key.startswith('_'):
                     fields.append(FieldInfo(
                        name=key,
                        type='string', # Guess
                        required=False, # Response fields are output
                        description='Auto-detected response field'
                    ))
        except Exception:
            pass
        return fields

    def _extract_field_info(self, field_name: str, field_obj) -> FieldInfo:
        """
        Extract information from a serializer field
        
        Args:
            field_name: Name of the field
            field_obj: Serializer field object
            
        Returns:
            FieldInfo object
        """
        field_type = type(field_obj).__name__
        
        # Map field types to more readable names
        type_mapping = {
            'CharField': 'string',
            'TextField': 'string',
            'EmailField': 'email',
            'URLField': 'url',
            'IntegerField': 'integer',
            'FloatField': 'float',
            'DecimalField': 'decimal',
            'BooleanField': 'boolean',
            'DateField': 'date',
            'DateTimeField': 'datetime',
            'TimeField': 'time',
            'UUIDField': 'uuid',
            'FileField': 'file',
            'ImageField': 'image',
            'ChoiceField': 'choice',
            'MultipleChoiceField': 'array',
            'ListField': 'array',
            'DictField': 'object',
            'JSONField': 'json',
            'PrimaryKeyRelatedField': 'integer (pk)',
            'SlugRelatedField': 'string (slug)',
            'HyperlinkedRelatedField': 'url',
            'StringRelatedField': 'string',
            'SerializerMethodField': 'any',
        }
        
        readable_type = type_mapping.get(field_type, field_type.lower())
        
        # Extract additional field properties
        required = getattr(field_obj, 'required', False)
        read_only = getattr(field_obj, 'read_only', False)
        write_only = getattr(field_obj, 'write_only', False)
        help_text = str(getattr(field_obj, 'help_text', '') or '')
        default = getattr(field_obj, 'default', None)
        
        # Handle choices
        choices = []
        if hasattr(field_obj, 'choices') and field_obj.choices:
            choices = list(dict(field_obj.choices).keys())
        
        # Handle validators for constraints
        max_length = getattr(field_obj, 'max_length', None)
        min_length = getattr(field_obj, 'min_length', None)
        max_value = getattr(field_obj, 'max_value', None)
        min_value = getattr(field_obj, 'min_value', None)
        
        # Handle nested serializers
        child_fields = []
        if hasattr(field_obj, 'child') and hasattr(field_obj.child, 'fields'):
            for child_name, child_field in field_obj.child.fields.items():
                child_fields.append(self._extract_field_info(child_name, child_field))
        elif hasattr(field_obj, 'fields'):
            for child_name, child_field in field_obj.fields.items():
                child_fields.append(self._extract_field_info(child_name, child_field))
        
        # Represent default value properly
        if default is not None and hasattr(default, '__class__'):
            if default.__class__.__name__ == 'empty':
                default = None
        
        return FieldInfo(
            name=field_name,
            field_type=readable_type,
            required=required,
            read_only=read_only,
            write_only=write_only,
            help_text=help_text,
            default=default,
            choices=choices,
            max_length=max_length,
            min_length=min_length,
            max_value=max_value,
            min_value=min_value,
            child_fields=child_fields,
        )
    
    def _get_query_params(self, view_class: Type) -> List[FieldInfo]:
        """
        Extract query parameters from filter backends
        
        Args:
            view_class: The view class
            
        Returns:
            List of FieldInfo for query parameters
        """
        query_params = []
        
        # Check for filter_backends
        filter_backends = getattr(view_class, 'filter_backends', [])
        
        # Check for filterset_fields
        filterset_fields = getattr(view_class, 'filterset_fields', [])
        if filterset_fields:
            for field_name in filterset_fields:
                query_params.append(FieldInfo(
                    name=field_name,
                    field_type='string',
                    help_text=f'Filter by {field_name}'
                ))
        
        # Check for search_fields
        search_fields = getattr(view_class, 'search_fields', [])
        if search_fields:
            query_params.append(FieldInfo(
                name='search',
                field_type='string',
                help_text=f'Search in: {", ".join(search_fields)}'
            ))
        
        # Check for ordering_fields
        ordering_fields = getattr(view_class, 'ordering_fields', [])
        if ordering_fields:
            if ordering_fields == '__all__':
                help_text = 'Order by any field (prefix with - for descending)'
            else:
                help_text = f'Order by: {", ".join(ordering_fields)}'
            query_params.append(FieldInfo(
                name='ordering',
                field_type='string',
                help_text=help_text
            ))
        
        # Add pagination params if applicable
        if hasattr(view_class, 'pagination_class') and view_class.pagination_class:
            query_params.extend([
                FieldInfo(name='page', field_type='integer', help_text='Page number'),
                FieldInfo(name='page_size', field_type='integer', help_text='Items per page'),
            ])
        
        return query_params
    
    def _get_view_description(self, view_class: Type, callback) -> str:
        """
        Get description from view docstring, cleaning up Body/Response sections
        """
        doc = ""
        # Try view class docstring first
        if view_class.__doc__:
            doc = view_class.__doc__.strip()
        # Try callback docstring
        elif callback.__doc__:
            doc = callback.__doc__.strip()
        
        if doc:
            # Clean description: Remove Body: and Response: blocks 
            # This prevents the raw JSON-like block from appearing in the main description
            if 'Body:' in doc or 'Request:' in doc:
                doc = re.split(r'(?:Body|Request)\s*:', doc, flags=re.IGNORECASE)[0].strip()
            elif 'Response:' in doc or 'Returns:' in doc:
                 doc = re.split(r'(?:Response|Returns)\s*:', doc, flags=re.IGNORECASE)[0].strip()
            return doc
        
        # Generate a default description
        view_name = view_class.__name__
        # Convert CamelCase to readable format
        readable_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', view_name)
        readable_name = readable_name.replace('View', '').replace('Viewset', '').strip()
        
        return f"{readable_name} endpoint"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert parsed data to dictionary format
        
        Returns:
            Dictionary containing all parsed API information
        """
        result = {
            'generated_at': None,  # Will be set by generator
            'apps': []
        }
        
        for app in self.parsed_apps:
            app_dict = {
                'name': app.app_name,
                'label': app.app_label,
                'description': app.description,
                'version': app.version,
                'endpoints': []
            }
            
            for endpoint in app.endpoints:
                endpoint_dict = {
                    'url': endpoint.url,
                    'name': endpoint.name,
                    'methods': endpoint.methods,
                    'view_class': endpoint.view_class,
                    'view_name': endpoint.view_name,
                    'description': endpoint.description,
                    'authentication': endpoint.authentication,
                    'permissions': endpoint.permissions,
                    'path_params': endpoint.path_params,
                    'tags': endpoint.tags,
                    'deprecated': endpoint.deprecated,
                    'request_body': {
                        'fields': [self._field_to_dict(f) for f in endpoint.request_fields]
                    },
                    'response': {
                        'fields': [self._field_to_dict(f) for f in endpoint.response_fields]
                    },
                    'query_params': [self._field_to_dict(f) for f in endpoint.query_params],
                }
                app_dict['endpoints'].append(endpoint_dict)
            
            result['apps'].append(app_dict)
        
        return result
    
    def _field_to_dict(self, field: FieldInfo) -> Dict[str, Any]:
        """Convert FieldInfo to dictionary"""
        d = {
            'name': field.name,
            'type': field.field_type,
            'required': field.required,
            'read_only': field.read_only,
            'write_only': field.write_only,
        }
        
        if field.help_text:
            d['help_text'] = field.help_text
        if field.default is not None:
            d['default'] = str(field.default)
        if field.choices:
            d['choices'] = field.choices
        if field.max_length:
            d['max_length'] = field.max_length
        if field.min_length:
            d['min_length'] = field.min_length
        if field.max_value is not None:
            d['max_value'] = field.max_value
        if field.min_value is not None:
            d['min_value'] = field.min_value
        if field.child_fields:
            d['children'] = [self._field_to_dict(f) for f in field.child_fields]
        
        return d
