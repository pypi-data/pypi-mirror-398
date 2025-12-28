"""
HTML Generator Module
Generates beautiful HTML documentation for APIs and WebSockets
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

from .parser import AppAPIInfo, EndpointInfo, FieldInfo


class HTMLGenerator:
    """
    Generates production-quality HTML documentation for APIs and WebSockets
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize HTML generator
        
        Args:
            config: Configuration dictionary with title, version, etc.
        """
        self.config = config or {}
        self.title = self.config.get('TITLE', 'API Documentation')
        self.version = self.config.get('VERSION', '1.0.0')
        self.description = self.config.get('DESCRIPTION', 'Complete API Reference')
        self.theme_color = self.config.get('THEME_COLOR', '#2563eb')
        
    def generate(self, apps: List[AppAPIInfo], output_path: str, 
                 websocket_apps: List = None) -> str:
        """
        Generate HTML documentation
        
        Args:
            apps: List of AppAPIInfo objects with parsed API data
            output_path: Path to save the HTML file
            websocket_apps: Optional list of WebSocketAppInfo objects
            
        Returns:
            Path to the generated HTML file
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        html_content = self._generate_html(apps, websocket_apps)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return os.path.abspath(output_path)
    
    def _generate_html(self, apps: List[AppAPIInfo], websocket_apps: List = None) -> str:
        """Generate complete HTML document"""
        
        sidebar_html = self._generate_sidebar(apps, websocket_apps)
        content_html = self._generate_content(apps, websocket_apps)
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: {self.theme_color};
            --primary-dark: color-mix(in srgb, {self.theme_color} 80%, black);
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --text-primary: #1f2937;
            --text-secondary: #4b5563;
            --text-muted: #6b7280;
            --border: #e5e7eb;
            --success: #22c55e;
            --warning: #f59e0b;
            --danger: #ef4444;
            --info: #3b82f6;
            --purple: #8b5cf6;
            --cyan: #06b6d4;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }}
        
        .container {{
            display: flex;
            min-height: 100vh;
        }}
        
        /* Sidebar */
        .sidebar {{
            width: 280px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            padding: 20px 0;
        }}
        
        .sidebar-header {{
            padding: 0 20px 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }}
        
        .sidebar-title {{
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 5px;
        }}
        
        .sidebar-version {{
            font-size: 0.75rem;
            color: var(--primary);
            background: rgba(37, 99, 235, 0.1);
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .nav-group {{
            margin-bottom: 20px;
        }}
        
        .nav-group-title {{
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0 20px;
            margin-bottom: 8px;
        }}
        
        .nav-item {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 8px 20px;
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 0.875rem;
            transition: all 0.15s;
        }}
        
        .nav-item:hover {{
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }}
        
        .nav-item.active {{
            background: rgba(37, 99, 235, 0.1);
            color: var(--primary);
            border-right: 2px solid var(--primary);
        }}
        
        .method-badge {{
            font-size: 0.625rem;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'JetBrains Mono', monospace;
            min-width: 45px;
            text-align: center;
        }}
        
        .method-GET {{ background: var(--success); color: white; }}
        .method-POST {{ background: var(--info); color: white; }}
        .method-PUT {{ background: var(--warning); color: white; }}
        .method-PATCH {{ background: var(--purple); color: white; }}
        .method-DELETE {{ background: var(--danger); color: white; }}
        .method-WS {{ background: var(--cyan); color: white; }}
        
        /* Main Content */
        .main-content {{
            flex: 1;
            margin-left: 280px;
            padding: 40px 60px;
            max-width: calc(100% - 280px);
        }}
        
        .header {{
            margin-bottom: 40px;
            padding-bottom: 25px;
            border-bottom: 1px solid var(--border);
        }}
        
        .header h1 {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: var(--text-primary);
        }}
        
        .header p {{
            color: var(--text-secondary);
            font-size: 1rem;
        }}
        
        .header-meta {{
            display: flex;
            gap: 20px;
            margin-top: 12px;
            font-size: 0.875rem;
            color: var(--text-muted);
        }}
        
        /* Sections */
        .section {{
            margin-bottom: 50px;
        }}
        
        .section-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border);
        }}
        
        .subsection-title {{
            font-size: 1.125rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 20px 0 12px 0;
        }}
        
        .small-header {{
            font-size: 0.9375rem;
            font-weight: 600;
            color: var(--text-primary);
            margin: 16px 0 8px 0;
        }}
        
        /* URL Box */
        .url-box {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 15px 0;
        }}
        
        .url-label {{
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .url-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.875rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 6px;
            color: var(--text-primary);
        }}
        
        /* Code Block */
        .code-block {{
            border: 1px solid var(--border);
            border-radius: 8px;
            margin: 12px 0;
            overflow: hidden;
        }}
        
        .code-header {{
            background: var(--bg-secondary);
            padding: 8px 15px;
            font-size: 0.75rem;
            color: var(--text-muted);
            border-bottom: 1px solid var(--border);
            font-family: 'JetBrains Mono', monospace;
        }}
        
        .code-content {{
            padding: 15px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            line-height: 1.6;
            overflow-x: auto;
            background: var(--bg-primary);
        }}
        
        .code-content pre {{
            margin: 0;
        }}
        
        /* Syntax highlighting */
        .json-key {{ color: #a31515; }}
        .json-string {{ color: #22863a; }}
        .json-number {{ color: #b5651d; }}
        .json-boolean {{ color: #7c3aed; }}
        .js-keyword {{ color: #7c3aed; }}
        .js-string {{ color: #22863a; }}
        .js-variable {{ color: #0550ae; }}
        
        /* Endpoint Card */
        .endpoint {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .endpoint-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 16px 20px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}
        
        .endpoint-methods {{
            display: flex;
            gap: 5px;
        }}
        
        .endpoint-url {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            color: var(--text-primary);
        }}
        
        .endpoint-body {{
            padding: 20px;
        }}
        
        .endpoint-description {{
            color: var(--text-secondary);
            margin-bottom: 16px;
        }}
        
        /* Info Grid */
        .info-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 16px;
        }}
        
        .info-item {{
            background: var(--bg-secondary);
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 0.875rem;
        }}
        
        .info-label {{
            font-weight: 600;
            color: var(--text-muted);
            margin-right: 6px;
        }}
        
        /* Fields Table */
        .fields-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
            margin: 12px 0;
        }}
        
        .fields-table th {{
            text-align: left;
            padding: 10px 12px;
            background: var(--bg-secondary);
            color: var(--text-muted);
            font-weight: 600;
            border-bottom: 1px solid var(--border);
        }}
        
        .fields-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }}
        
        .fields-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .field-name {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--primary);
        }}
        
        .field-type {{
            color: var(--purple);
            font-size: 0.8rem;
        }}
        
        /* Feature List */
        .feature-list {{
            list-style: none;
            padding: 0;
            margin: 12px 0;
        }}
        
        .feature-list li {{
            padding: 6px 0;
            padding-left: 20px;
            position: relative;
            color: var(--text-secondary);
        }}
        
        .feature-list li::before {{
            content: '•';
            position: absolute;
            left: 0;
            color: var(--primary);
            font-weight: bold;
        }}
        
        /* Action Card */
        .action-card {{
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .action-title {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 10px;
        }}
        
        /* Connection Errors Table */
        .error-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
        }}
        
        .error-table th, .error-table td {{
            padding: 10px 15px;
            text-align: left;
            border: 1px solid var(--border);
        }}
        
        .error-table th {{
            background: var(--bg-secondary);
            font-weight: 600;
            color: var(--text-muted);
        }}
        
        .error-code {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--danger);
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .sidebar {{
                display: none;
            }}
            
            .main-content {{
                margin-left: 0;
                max-width: 100%;
                padding: 20px;
            }}
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-secondary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        {sidebar_html}
        <main class="main-content">
            <div class="header">
                <h1>{self.title}</h1>
                <p>{self.description}</p>
                <div class="header-meta">
                    <span>📌 Version {self.version}</span>
                    <span>📅 Generated on {datetime.now().strftime("%B %d, %Y")}</span>
                </div>
            </div>
            
            {content_html}
        </main>
    </div>
    
    <script>
        // Smooth scrolling
        document.querySelectorAll('.nav-item').forEach(link => {{
            link.addEventListener('click', function(e) {{
                const href = this.getAttribute('href');
                if (href.startsWith('#')) {{
                    e.preventDefault();
                    const target = document.querySelector(href);
                    if (target) {{
                        target.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                    }}
                }}
            }});
        }});
        
        // Active section highlighting
        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    const id = entry.target.id;
                    document.querySelectorAll('.nav-item').forEach(link => {{
                        link.classList.remove('active');
                        if (link.getAttribute('href') === '#' + id) {{
                            link.classList.add('active');
                        }}
                    }});
                }}
            }});
        }}, {{ threshold: 0.3 }});
        
        document.querySelectorAll('.endpoint, .section').forEach(el => {{
            if (el.id) observer.observe(el);
        }});
    </script>
</body>
</html>'''
    
    def _generate_sidebar(self, apps: List[AppAPIInfo], websocket_apps: List = None) -> str:
        """Generate sidebar navigation HTML"""
        nav_items = []
        
        # REST API endpoints
        for app in apps:
            nav_items.append(f'''
            <div class="nav-group">
                <div class="nav-group-title">📦 {app.app_label}</div>
            ''')
            
            for endpoint in app.endpoints:
                endpoint_id = self._generate_id(app.app_name, endpoint.url)
                methods_html = ''.join([
                    f'<span class="method-badge method-{m}">{m}</span>' 
                    for m in endpoint.methods[:2]
                ])
                
                short_url = endpoint.url if len(endpoint.url) <= 25 else endpoint.url[:22] + '...'
                
                nav_items.append(f'''
                <a href="#{endpoint_id}" class="nav-item">
                    {methods_html}
                    <span>{short_url}</span>
                </a>
                ''')
            
            nav_items.append('</div>')
        
        # WebSocket endpoints
        if websocket_apps:
            for ws_app in websocket_apps:
                nav_items.append(f'''
                <div class="nav-group">
                    <div class="nav-group-title">🔌 {ws_app.app_label} WebSocket</div>
                ''')
                
                for endpoint in ws_app.endpoints:
                    endpoint_id = self._generate_id(ws_app.app_name, endpoint.name)
                    
                    nav_items.append(f'''
                    <a href="#{endpoint_id}" class="nav-item">
                        <span class="method-badge method-WS">WS</span>
                        <span>{endpoint.name}</span>
                    </a>
                    ''')
                
                nav_items.append('</div>')
        
        return f'''
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">{self.title}</div>
                <span class="sidebar-version">v{self.version}</span>
            </div>
            {''.join(nav_items)}
        </aside>
        '''
    
    def _generate_content(self, apps: List[AppAPIInfo], websocket_apps: List = None) -> str:
        """Generate main content HTML"""
        content = []
        
        # REST API content
        for app in apps:
            endpoints_html = []
            
            for endpoint in app.endpoints:
                endpoint_html = self._generate_endpoint(app.app_name, endpoint)
                endpoints_html.append(endpoint_html)
            
            content.append(f'''
            <section class="section" id="app-{app.app_name}">
                <h2 class="section-title">📦 {app.app_label}</h2>
                <p style="color: var(--text-secondary); margin-bottom: 20px;">
                    {app.description or f"API endpoints for {app.app_label}"}
                </p>
                {''.join(endpoints_html)}
            </section>
            ''')
        
        # WebSocket API content
        if websocket_apps:
            for ws_app in websocket_apps:
                for endpoint in ws_app.endpoints:
                    ws_html = self._generate_websocket_endpoint(ws_app, endpoint)
                    content.append(ws_html)
        
        return ''.join(content)
    
    def _generate_endpoint(self, app_name: str, endpoint: EndpointInfo) -> str:
        """Generate HTML for a single REST endpoint"""
        endpoint_id = self._generate_id(app_name, endpoint.url)
        
        methods_html = ''.join([
            f'<span class="method-badge method-{m}">{m}</span>' 
            for m in endpoint.methods
        ])
        
        # Info items
        info_items = []
        if endpoint.authentication:
            info_items.append(f'''
            <div class="info-item">
                <span class="info-label">🔐 Auth:</span>
                {', '.join(endpoint.authentication)}
            </div>
            ''')
        if endpoint.permissions:
            info_items.append(f'''
            <div class="info-item">
                <span class="info-label">🛡️ Permissions:</span>
                {', '.join(endpoint.permissions)}
            </div>
            ''')
        
        info_grid = f'<div class="info-grid">{"".join(info_items)}</div>' if info_items else ''
        
        # Request body
        request_html = ''
        if endpoint.request_fields:
            request_html = self._generate_fields_section(
                'Request Body', endpoint.request_fields, show_example=True
            )
        
        # Response
        response_html = ''
        if endpoint.response_fields:
            response_html = self._generate_fields_section(
                'Response (200 OK)', endpoint.response_fields, show_example=True, is_response=True
            )
        
        return f'''
        <div class="endpoint" id="{endpoint_id}">
            <div class="endpoint-header">
                <div class="endpoint-methods">{methods_html}</div>
                <div class="endpoint-url">{endpoint.url}</div>
            </div>
            <div class="endpoint-body">
                <p class="endpoint-description">{endpoint.description}</p>
                {info_grid}
                {request_html}
                {response_html}
            </div>
        </div>
        '''
    
    def _generate_websocket_endpoint(self, ws_app, endpoint) -> str:
        """Generate HTML for a WebSocket endpoint"""
        endpoint_id = self._generate_id(ws_app.app_name, endpoint.name)
        
        # Features list
        features_html = ''
        if endpoint.features:
            features_items = ''.join([f'<li>{f}</li>' for f in endpoint.features])
            features_html = f'''
            <div class="small-header">Features:</div>
            <ul class="feature-list">{features_items}</ul>
            '''
        
        # URL box
        full_url = f"{ws_app.base_url}{endpoint.url}?token={{jwt_token}}"
        url_html = f'''
        <div class="url-box">
            <span class="url-label">WebSocket URL:</span>
            <span class="url-value">{full_url}</span>
        </div>
        '''
        
        # Connection code
        js_code = f"const ws = new WebSocket('{ws_app.base_url}{endpoint.url}?token=YOUR_JWT_TOKEN');"
        connection_html = f'''
        <div class="subsection-title">1. Establishing Connection</div>
        <div class="small-header">Client Action:</div>
        {self._create_code_block(js_code, 'javascript')}
        '''
        
        # Connection response
        if endpoint.connection_response:
            response_json = json.dumps(endpoint.connection_response, indent=2)
        else:
            response_json = json.dumps({
                "type": "connection_established",
                "user_id": 123,
                "timestamp": "2025-01-15T10:30:00.000Z"
            }, indent=2)
        
        connection_html += f'''
        <div class="small-header">Server Response (on success):</div>
        {self._create_code_block(response_json, 'json')}
        '''
        
        # Connection errors
        errors_html = ''
        if endpoint.disconnect_codes:
            error_rows = ''.join([
                f'<tr><td class="error-code">{c["code"]}</td><td>{c["description"]}</td></tr>'
                for c in endpoint.disconnect_codes
            ])
            errors_html = f'''
            <div class="small-header">Connection Errors:</div>
            <table class="error-table">
                <thead><tr><th>Code</th><th>Description</th></tr></thead>
                <tbody>{error_rows}</tbody>
            </table>
            '''
        
        # Actions
        actions_html = ''
        if endpoint.actions:
            action_cards = []
            for i, action in enumerate(endpoint.actions, 1):
                request_json = json.dumps(action.example_request, indent=2) if action.example_request else '{}'
                response_json = json.dumps(action.example_response, indent=2) if action.example_response else '{}'
                
                action_cards.append(f'''
                <div class="action-card">
                    <div class="action-title">{i}. {action.name.replace('_', ' ').title()}</div>
                    <p style="color: var(--text-secondary); margin-bottom: 12px;">{action.description}</p>
                    <div class="small-header">Client sends:</div>
                    {self._create_code_block(request_json, 'json')}
                    <div class="small-header">Server broadcasts:</div>
                    {self._create_code_block(response_json, 'json')}
                </div>
                ''')
            
            actions_html = f'''
            <div class="subsection-title">Client Actions (Client → Server)</div>
            {''.join(action_cards)}
            '''
        
        # Server events
        events_html = ''
        if endpoint.server_events:
            event_cards = []
            for event in endpoint.server_events:
                response_json = json.dumps(event.example_response, indent=2) if event.example_response else '{}'
                
                event_cards.append(f'''
                <div class="action-card">
                    <div class="action-title">• {event.name.replace('_', ' ').title()}</div>
                    <p style="color: var(--text-secondary); margin-bottom: 12px;">{event.description}</p>
                    {self._create_code_block(response_json, 'json')}
                </div>
                ''')
            
            events_html = f'''
            <div class="subsection-title">Server Events (Server → Client)</div>
            {''.join(event_cards)}
            '''
        
        return f'''
        <section class="section" id="{endpoint_id}">
            <h2 class="section-title">🔌 {endpoint.name} WebSocket API Documentation</h2>
            
            <div class="subsection-title">Overview</div>
            <p style="color: var(--text-secondary);">{endpoint.description}</p>
            {features_html}
            {url_html}
            
            <hr style="border: none; border-top: 1px solid var(--border); margin: 25px 0;">
            
            <div class="subsection-title" style="font-size: 1.25rem; margin-bottom: 15px;">Connection Lifecycle</div>
            {connection_html}
            {errors_html}
            
            {actions_html}
            {events_html}
        </section>
        '''
    
    def _generate_fields_section(self, title: str, fields: List[FieldInfo], 
                                  show_example: bool = False, is_response: bool = False) -> str:
        """Generate a fields section with table and optional JSON example"""
        rows = []
        for field in fields:
            if is_response and field.write_only:
                continue
            if not is_response and field.read_only:
                continue
            
            req_text = '<span style="color: var(--danger);">Required</span>' if field.required else '<span style="color: var(--text-muted);">Optional</span>'
            desc = field.help_text if field.help_text else '—'
            
            rows.append(f'''
            <tr>
                <td><span class="field-name">{field.name}</span></td>
                <td><span class="field-type">{field.field_type}</span></td>
                <td>{req_text}</td>
                <td>{desc}</td>
            </tr>
            ''')
        
        table_html = f'''
        <table class="fields-table">
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Type</th>
                    <th>Required</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows)}
            </tbody>
        </table>
        '''
        
        example_html = ''
        if show_example:
            json_example = self._create_json_example(fields, not is_response)
            example_html = self._create_code_block(json_example, 'json')
        
        return f'''
        <div style="margin-top: 16px;">
            <div class="small-header">{title}</div>
            {table_html}
            {example_html}
        </div>
        '''
    
    def _create_code_block(self, code: str, language: str) -> str:
        """Create a styled code block"""
        highlighted_code = self._highlight_code(code, language)
        return f'''
        <div class="code-block">
            <div class="code-header">{language}</div>
            <div class="code-content"><pre>{highlighted_code}</pre></div>
        </div>
        '''
    
    def _highlight_code(self, code: str, language: str) -> str:
        """Add syntax highlighting to code"""
        import re
        
        if language == 'json':
            # Keys
            code = re.sub(r'"([^"]+)":', r'<span class="json-key">"\1"</span>:', code)
            # String values
            code = re.sub(r': "([^"]*)"', r': <span class="json-string">"\1"</span>', code)
            # Numbers
            code = re.sub(r': (\d+\.?\d*)', r': <span class="json-number">\1</span>', code)
            # Booleans/null
            code = re.sub(r': (true|false|null)', r': <span class="json-boolean">\1</span>', code)
            
        elif language == 'javascript':
            # Keywords
            code = re.sub(r'\b(const|let|var|new|function|return)\b', 
                         r'<span class="js-keyword">\1</span>', code)
            # Strings
            code = re.sub(r"('[^']*')", r'<span class="js-string">\1</span>', code)
        
        return code
    
    def _create_json_example(self, fields: List[FieldInfo], is_request: bool = True) -> str:
        """Generate JSON example from fields"""
        example = {}
        
        for field in fields:
            if is_request and field.read_only:
                continue
            if not is_request and field.write_only:
                continue
            
            value = self._get_example_value(field)
            example[field.name] = value
        
        return json.dumps(example, indent=2)
    
    def _get_example_value(self, field: FieldInfo) -> Any:
        """Get example value for a field"""
        if field.choices:
            return field.choices[0] if field.choices else None
        
        type_examples = {
            'string': 'example_string',
            'email': 'user@example.com',
            'url': 'https://example.com',
            'integer': 1,
            'float': 1.0,
            'decimal': '1.00',
            'boolean': True,
            'date': '2025-01-15',
            'datetime': '2025-01-15T10:30:00Z',
            'time': '10:30:00',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
        }
        
        base_type = field.field_type.lower()
        return type_examples.get(base_type, f'example_{field.name}')
    
    def _generate_id(self, app_name: str, identifier: str) -> str:
        """Generate a valid HTML ID"""
        import re
        id_str = f"{app_name}-{identifier}"
        id_str = re.sub(r'[^a-zA-Z0-9-]', '-', id_str)
        id_str = re.sub(r'-+', '-', id_str)
        return id_str.strip('-').lower()
