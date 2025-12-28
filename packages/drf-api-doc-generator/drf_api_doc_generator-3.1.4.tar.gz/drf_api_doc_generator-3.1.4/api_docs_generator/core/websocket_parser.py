"""
WebSocket Parser Module
Extracts WebSocket consumer information from Django Channels applications
"""

import ast
import os
import re
import inspect
from typing import Dict, List, Any, Optional, Type
from dataclasses import dataclass, field


@dataclass
class WebSocketAction:
    """Information about a WebSocket action/message type"""
    name: str
    action_type: str  # 'client_to_server' or 'server_to_client'
    description: str = ""
    request_schema: Dict[str, Any] = field(default_factory=dict)
    response_schema: Dict[str, Any] = field(default_factory=dict)
    example_request: Dict[str, Any] = field(default_factory=dict)
    example_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebSocketEndpoint:
    """Information about a WebSocket endpoint"""
    url: str
    name: str
    consumer_class: str
    description: str = ""
    authentication: List[str] = field(default_factory=list)
    connection_params: List[Dict[str, str]] = field(default_factory=list)
    connection_response: Dict[str, Any] = field(default_factory=dict)
    disconnect_codes: List[Dict[str, str]] = field(default_factory=list)
    actions: List[WebSocketAction] = field(default_factory=list)
    server_events: List[WebSocketAction] = field(default_factory=list)
    features: List[str] = field(default_factory=list)


@dataclass
class WebSocketAppInfo:
    """Complete WebSocket information for an app"""
    app_name: str
    app_label: str
    description: str
    version: str
    base_url: str = "ws://domain"
    endpoints: List[WebSocketEndpoint] = field(default_factory=list)


class WebSocketParser:
    """
    Parser to extract WebSocket information from Django Channels consumers
    """
    
    def __init__(self, consumer_files: List[str] = None, config: Dict = None):
        """
        Initialize the parser
        
        Args:
            consumer_files: List of file paths containing consumers
            config: Configuration dictionary
        """
        self.consumer_files = consumer_files or []
        self.config = config or {}
        self.parsed_apps: List[WebSocketAppInfo] = []
    
    def parse_from_file(self, file_path: str) -> WebSocketAppInfo:
        """
        Parse WebSocket consumers from a Python file
        
        Args:
            file_path: Path to the consumer file
            
        Returns:
            WebSocketAppInfo object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_from_content(content, file_path)
    
    def parse_from_content(self, content: str, source_name: str = "unknown") -> WebSocketAppInfo:
        """
        Parse WebSocket consumers from Python code content
        
        Args:
            content: Python source code
            source_name: Name of the source for labeling
            
        Returns:
            WebSocketAppInfo object
        """
        # Extract app name from path or default
        app_name = self._extract_app_name(source_name)
        
        app_info = WebSocketAppInfo(
            app_name=app_name,
            app_label=app_name.replace('_', ' ').title(),
            description="WebSocket API Documentation",
            version=self.config.get('VERSION', '1.0.0'),
            base_url=self.config.get('WS_BASE_URL', 'ws://domain')
        )
        
        # Parse the AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Warning: Could not parse {source_name}: {e}")
            return app_info
        
        # Find all consumer classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if self._is_consumer_class(node, content):
                    endpoint = self._parse_consumer_class(node, content)
                    if endpoint:
                        app_info.endpoints.append(endpoint)
        
        self.parsed_apps.append(app_info)
        return app_info
    
    def _extract_app_name(self, source: str) -> str:
        """Extract app name from file path"""
        parts = source.replace('\\', '/').split('/')
        for i, part in enumerate(parts):
            if part in ['consumers', 'consumers.py']:
                if i > 0:
                    return parts[i-1]
        return "websocket"
    
    def _is_consumer_class(self, node: ast.ClassDef, content: str) -> bool:
        """Check if a class is a WebSocket consumer"""
        consumer_bases = [
            'WebsocketConsumer', 'AsyncWebsocketConsumer',
            'JsonWebsocketConsumer', 'AsyncJsonWebsocketConsumer'
        ]
        
        # Check base classes
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in consumer_bases:
                return True
            if isinstance(base, ast.Attribute) and base.attr in consumer_bases:
                return True
        
        # Also check if class name contains 'Consumer' and has connect/receive methods
        if 'Consumer' in node.name:
            method_names = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_names.append(item.name)
            
            # Check for WebSocket-like methods
            if 'connect' in method_names or 'receive_json' in method_names or 'receive' in method_names:
                return True
        
        return False
    
    def _parse_consumer_class(self, node: ast.ClassDef, content: str) -> Optional[WebSocketEndpoint]:
        """Parse a consumer class and extract endpoint information"""
        
        # Get class docstring
        docstring = ast.get_docstring(node) or ""
        
        # Extract features from docstring
        features = self._extract_features_from_docstring(docstring)
        
        # Find handler methods
        actions = []
        action_names_seen = set()
        server_events = []
        connection_response = {}
        disconnect_codes = []
        
        for item in node.body:
            if isinstance(item, ast.AsyncFunctionDef) or isinstance(item, ast.FunctionDef):
                method_name = item.name
                method_doc = ast.get_docstring(item) or ""
                
                if method_name == 'connect':
                    connection_response = self._extract_connection_response(item, content)
                    disconnect_codes = self._extract_disconnect_codes(item, content)
                    
                elif method_name == 'receive_json' or method_name == 'receive':
                    # Extract actions from receive handler (skip - prefer handle_ methods)
                    pass
                    
                elif method_name.startswith('handle_'):
                    # Individual action handler - prefer these
                    action_name = method_name.replace('handle_', '')
                    if action_name not in action_names_seen:
                        action = self._parse_action_handler(item, action_name, content)
                        if action:
                            actions.append(action)
                            action_names_seen.add(action_name)
                        
                elif method_name in ['chat_message', 'user_typing', 'user_recording', 
                                     'messages_read', 'group_message']:
                    # Server-to-client event
                    event = self._parse_server_event(item, method_name, content)
                    if event:
                        server_events.append(event)
        
        # Determine URL from class name
        url = self._generate_url_from_class_name(node.name)
        
        return WebSocketEndpoint(
            url=url,
            name=node.name,
            consumer_class=node.name,
            description=docstring.split('\n')[0] if docstring else f"{node.name} WebSocket endpoint",
            authentication=self._extract_auth_from_content(content),
            connection_params=self._extract_connection_params(node, content),
            connection_response=connection_response,
            disconnect_codes=disconnect_codes,
            actions=actions,
            server_events=server_events,
            features=features
        )
    
    def _extract_features_from_docstring(self, docstring: str) -> List[str]:
        """Extract features list from docstring"""
        features = []
        in_features = False
        
        for line in docstring.split('\n'):
            line = line.strip()
            if 'Features:' in line:
                in_features = True
                continue
            if in_features:
                if line.startswith('-'):
                    features.append(line[1:].strip())
                elif line and not line.startswith(' '):
                    break
        
        return features
    
    def _extract_connection_response(self, node: ast.FunctionDef, content: str) -> Dict:
        """Extract connection response schema from connect method"""
        # Look for send_json patterns
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                if hasattr(item, 'func'):
                    func = item.func
                    if isinstance(func, ast.Attribute) and func.attr == 'send_json':
                        # Try to extract the dict being sent
                        if item.args:
                            return self._dict_from_ast(item.args[0], content)
        return {}
    
    def _extract_disconnect_codes(self, node: ast.FunctionDef, content: str) -> List[Dict]:
        """Extract disconnect/close codes from connect method"""
        codes = []
        
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                if hasattr(item, 'func'):
                    func = item.func
                    if isinstance(func, ast.Attribute) and func.attr == 'close':
                        for kw in item.keywords:
                            if kw.arg == 'code' and isinstance(kw.value, ast.Constant):
                                codes.append({
                                    'code': str(kw.value.value),
                                    'description': self._get_close_code_description(kw.value.value)
                                })
        
        return codes
    
    def _get_close_code_description(self, code: int) -> str:
        """Get description for WebSocket close code"""
        descriptions = {
            4400: "Bad Request - Invalid parameters",
            4401: "Unauthorized - Authentication required",
            4403: "Forbidden - Access denied",
            4404: "Not Found - Resource not found",
            4409: "Conflict - Resource conflict",
        }
        return descriptions.get(code, f"Close code {code}")
    
    def _extract_actions_from_receive(self, node: ast.FunctionDef, content: str) -> List[WebSocketAction]:
        """Extract action handlers from receive_json method"""
        actions = []
        
        # Look for handlers dict or if/elif chains
        for item in ast.walk(node):
            if isinstance(item, ast.Dict):
                # Found handlers dictionary
                for i, key in enumerate(item.keys):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str):
                        action_name = key.value
                        actions.append(WebSocketAction(
                            name=action_name,
                            action_type='client_to_server',
                            description=f"Handle {action_name.replace('_', ' ')} action",
                            request_schema=self._get_action_request_schema(action_name),
                            response_schema=self._get_action_response_schema(action_name),
                            example_request=self._get_action_example_request(action_name),
                            example_response=self._get_action_example_response(action_name)
                        ))
        
        return actions
    
    def _parse_action_handler(self, node: ast.FunctionDef, action_name: str, 
                              content: str) -> Optional[WebSocketAction]:
        """Parse an individual action handler method"""
        docstring = ast.get_docstring(node) or ""
        
        # Extract request schema from docstring or method body
        request_schema = self._extract_schema_from_docstring(docstring, 'Client sends:')
        if not request_schema:
            request_schema = self._get_action_request_schema(action_name)
        
        response_schema = self._extract_schema_from_docstring(docstring, 'Server responds:')
        if not response_schema:
            response_schema = self._get_action_response_schema(action_name)
        
        return WebSocketAction(
            name=action_name,
            action_type='client_to_server',
            description=docstring.split('\n')[0] if docstring else f"Handle {action_name}",
            request_schema=request_schema,
            response_schema=response_schema,
            example_request=self._get_action_example_request(action_name),
            example_response=self._get_action_example_response(action_name)
        )
    
    def _parse_server_event(self, node: ast.FunctionDef, event_name: str, 
                            content: str) -> Optional[WebSocketAction]:
        """Parse a server-to-client event handler"""
        docstring = ast.get_docstring(node) or ""
        
        return WebSocketAction(
            name=event_name,
            action_type='server_to_client',
            description=docstring.split('\n')[0] if docstring else f"Server event: {event_name}",
            response_schema=self._get_server_event_schema(event_name),
            example_response=self._get_server_event_example(event_name)
        )
    
    def _extract_schema_from_docstring(self, docstring: str, marker: str) -> Dict:
        """Extract JSON schema from docstring"""
        # Simple extraction - look for JSON block after marker
        if marker in docstring:
            try:
                start = docstring.index(marker) + len(marker)
                # Find JSON block
                brace_start = docstring.index('{', start)
                brace_count = 1
                i = brace_start + 1
                while i < len(docstring) and brace_count > 0:
                    if docstring[i] == '{':
                        brace_count += 1
                    elif docstring[i] == '}':
                        brace_count -= 1
                    i += 1
                json_str = docstring[brace_start:i]
                import json
                return json.loads(json_str)
            except:
                pass
        return {}
    
    def _dict_from_ast(self, node: ast.AST, content: str) -> Dict:
        """Convert AST dict node to Python dict"""
        if isinstance(node, ast.Dict):
            result = {}
            for i, key in enumerate(node.keys):
                if isinstance(key, ast.Constant):
                    key_val = key.value
                    val_node = node.values[i]
                    if isinstance(val_node, ast.Constant):
                        result[key_val] = val_node.value
                    elif isinstance(val_node, ast.Dict):
                        result[key_val] = self._dict_from_ast(val_node, content)
                    else:
                        result[key_val] = "<dynamic>"
            return result
        return {}
    
    def _generate_url_from_class_name(self, class_name: str) -> str:
        """Generate URL pattern from class name"""
        # Remove 'Consumer' suffix
        name = class_name.replace('Consumer', '')
        
        # Check for common patterns BEFORE converting to url_part
        name_lower = name.lower()
        if name_lower == 'dm' or 'dm' in name_lower.split():
            return "/ws/dm/{peer_id}/"
        elif 'group' in name_lower:
            return "/ws/group/{group_id}/"
        elif 'chat' in name_lower:
            return "/ws/chat/{room_id}/"
        elif 'notification' in name_lower:
            return "/ws/notifications/"
        elif 'event' in name_lower:
            return "/ws/events/"
        
        # Convert CamelCase to path format
        url_part = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        
        return f"/ws/{url_part}/"
    
    def _extract_auth_from_content(self, content: str) -> List[str]:
        """Extract authentication info from content"""
        auth = []
        
        if 'is_authenticated' in content:
            auth.append("JWT Token (via query param or header)")
        if 'token' in content.lower():
            auth.append("Token Authentication")
        
        return auth if auth else ["None specified"]
    
    def _extract_connection_params(self, node: ast.ClassDef, content: str) -> List[Dict]:
        """Extract connection parameters"""
        params = []
        
        # Look for URL parameters
        if 'peer_id' in content:
            params.append({
                'name': 'peer_id',
                'type': 'integer',
                'description': 'User ID of the peer to connect with',
                'required': True
            })
        if 'room_id' in content or 'group_id' in content:
            params.append({
                'name': 'room_id',
                'type': 'string',
                'description': 'Room/Group identifier',
                'required': True
            })
        if 'token' in content.lower():
            params.append({
                'name': 'token',
                'type': 'string',
                'description': 'JWT authentication token',
                'required': True
            })
        
        return params
    
    def _get_action_request_schema(self, action_name: str) -> Dict:
        """Get default request schema for known actions"""
        schemas = {
            'send_message': {
                'action': 'string (required)',
                'encrypted_content': 'string (required)',
                'msg_type': 'string (default: "text")',
                'client_msg_id': 'string (optional)',
                'nonce': 'string (optional)',
                'reply_to_id': 'integer (optional)',
                'media_url': 'string (optional)',
                'thumbnail_url': 'string (optional)',
                'file_name': 'string (optional)',
                'file_size': 'integer (optional)',
                'duration': 'integer (optional)'
            },
            'typing_start': {
                'action': 'string (required)'
            },
            'typing_stop': {
                'action': 'string (required)'
            },
            'recording_start': {
                'action': 'string (required)'
            },
            'recording_stop': {
                'action': 'string (required)'
            },
            'mark_read': {
                'action': 'string (required)',
                'message_id': 'integer (required)'
            }
        }
        return schemas.get(action_name, {'action': 'string (required)'})
    
    def _get_action_response_schema(self, action_name: str) -> Dict:
        """Get default response schema for known actions"""
        schemas = {
            'send_message': {
                'type': 'message',
                'conversation_id': 'integer',
                'message': {
                    'id': 'integer',
                    'sender_id': 'integer',
                    'msg_type': 'string',
                    'encrypted_content': 'string',
                    'created_at': 'datetime'
                }
            },
            'typing_start': {
                'type': 'typing',
                'user_id': 'integer',
                'is_typing': 'boolean'
            },
            'mark_read': {
                'type': 'read_receipt',
                'user_id': 'integer',
                'last_read_message_id': 'integer'
            }
        }
        return schemas.get(action_name, {'type': 'string'})
    
    def _get_action_example_request(self, action_name: str) -> Dict:
        """Get example request for action"""
        examples = {
            'send_message': {
                'action': 'send_message',
                'encrypted_content': 'base64_encrypted_content_here',
                'msg_type': 'text',
                'client_msg_id': 'uuid-v4-string',
                'nonce': 'random_nonce_string'
            },
            'typing_start': {
                'action': 'typing_start'
            },
            'typing_stop': {
                'action': 'typing_stop'
            },
            'recording_start': {
                'action': 'recording_start'
            },
            'recording_stop': {
                'action': 'recording_stop'
            },
            'mark_read': {
                'action': 'mark_read',
                'message_id': 12345
            }
        }
        return examples.get(action_name, {'action': action_name})
    
    def _get_action_example_response(self, action_name: str) -> Dict:
        """Get example response for action"""
        examples = {
            'send_message': {
                'type': 'message',
                'conversation_id': 1,
                'message': {
                    'id': 123,
                    'conversation_id': 1,
                    'sender_id': 42,
                    'sender': {
                        'id': 42,
                        'username': 'john_doe'
                    },
                    'msg_type': 'text',
                    'encrypted_content': 'base64_encrypted_content',
                    'nonce': 'random_nonce',
                    'created_at': '2025-01-15T10:30:00.000Z',
                    'client_msg_id': 'uuid-v4-string'
                }
            },
            'typing_start': {
                'type': 'typing',
                'conversation_id': 1,
                'user_id': 42,
                'username': 'john_doe',
                'is_typing': True
            },
            'typing_stop': {
                'type': 'typing',
                'conversation_id': 1,
                'user_id': 42,
                'username': 'john_doe',
                'is_typing': False
            },
            'mark_read': {
                'type': 'read_receipt',
                'conversation_id': 1,
                'user_id': 42,
                'last_read_message_id': 12345,
                'read_at': '2025-01-15T10:35:00.000Z'
            }
        }
        return examples.get(action_name, {'type': action_name})
    
    def _get_server_event_schema(self, event_name: str) -> Dict:
        """Get schema for server events"""
        schemas = {
            'chat_message': {
                'type': 'message',
                'conversation_id': 'integer',
                'message': 'object'
            },
            'user_typing': {
                'type': 'typing',
                'user_id': 'integer',
                'is_typing': 'boolean'
            },
            'user_recording': {
                'type': 'recording',
                'user_id': 'integer',
                'is_recording': 'boolean'
            },
            'messages_read': {
                'type': 'read_receipt',
                'user_id': 'integer',
                'last_read_message_id': 'integer'
            }
        }
        return schemas.get(event_name, {'type': 'string'})
    
    def _get_server_event_example(self, event_name: str) -> Dict:
        """Get example for server events"""
        examples = {
            'chat_message': {
                'type': 'message',
                'conversation_id': 1,
                'message': {
                    'id': 123,
                    'sender_id': 42,
                    'content': 'Hello!'
                }
            },
            'user_typing': {
                'type': 'typing',
                'conversation_id': 1,
                'user_id': 42,
                'username': 'john_doe',
                'is_typing': True
            },
            'user_recording': {
                'type': 'recording',
                'conversation_id': 1,
                'user_id': 42,
                'username': 'john_doe',
                'is_recording': True
            },
            'messages_read': {
                'type': 'read_receipt',
                'conversation_id': 1,
                'user_id': 42,
                'last_read_message_id': 100,
                'read_at': '2025-01-15T10:30:00Z'
            }
        }
        return examples.get(event_name, {'type': event_name})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parsed data to dictionary format"""
        result = {
            'websocket_apis': []
        }
        
        for app in self.parsed_apps:
            app_dict = {
                'app_name': app.app_name,
                'app_label': app.app_label,
                'description': app.description,
                'version': app.version,
                'base_url': app.base_url,
                'endpoints': []
            }
            
            for endpoint in app.endpoints:
                endpoint_dict = {
                    'url': endpoint.url,
                    'name': endpoint.name,
                    'consumer_class': endpoint.consumer_class,
                    'description': endpoint.description,
                    'authentication': endpoint.authentication,
                    'connection_params': endpoint.connection_params,
                    'connection_response': endpoint.connection_response,
                    'disconnect_codes': endpoint.disconnect_codes,
                    'features': endpoint.features,
                    'actions': [
                        {
                            'name': a.name,
                            'type': a.action_type,
                            'description': a.description,
                            'request_schema': a.request_schema,
                            'response_schema': a.response_schema,
                            'example_request': a.example_request,
                            'example_response': a.example_response
                        }
                        for a in endpoint.actions
                    ],
                    'server_events': [
                        {
                            'name': e.name,
                            'type': e.action_type,
                            'description': e.description,
                            'response_schema': e.response_schema,
                            'example_response': e.example_response
                        }
                        for e in endpoint.server_events
                    ]
                }
                app_dict['endpoints'].append(endpoint_dict)
            
            result['websocket_apis'].append(app_dict)
        
        return result
