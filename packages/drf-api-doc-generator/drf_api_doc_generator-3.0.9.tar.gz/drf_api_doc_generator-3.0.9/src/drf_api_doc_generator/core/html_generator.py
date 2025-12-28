"""
HTML Generator Module
Generates beautiful HTML documentation for APIs
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any

from .parser import AppAPIInfo, EndpointInfo, FieldInfo


class HTMLGenerator:
    """
    Generates production-quality HTML documentation for APIs
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
        
    def generate(self, apps: List[AppAPIInfo], output_path: str) -> str:
        """
        Generate HTML documentation
        
        Args:
            apps: List of AppAPIInfo objects with parsed API data
            output_path: Path to save the HTML file
            
        Returns:
            Path to the generated HTML file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        html_content = self._generate_html(apps)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return os.path.abspath(output_path)
    
    def _generate_html(self, apps: List[AppAPIInfo]) -> str:
        """Generate complete HTML document"""
        
        # Generate sidebar navigation
        sidebar_html = self._generate_sidebar(apps)
        
        # Generate main content
        content_html = self._generate_content(apps)
        
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
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: #334155;
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
        .method-HEAD {{ background: var(--text-muted); color: white; }}
        .method-OPTIONS {{ background: var(--cyan); color: white; }}
        
        /* Main Content */
        .main-content {{
            flex: 1;
            margin-left: 280px;
            padding: 40px 60px;
            max-width: calc(100% - 280px);
        }}
        
        .header {{
            margin-bottom: 50px;
            padding-bottom: 30px;
            border-bottom: 1px solid var(--border);
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, var(--primary), var(--cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header p {{
            color: var(--text-secondary);
            font-size: 1.125rem;
        }}
        
        .header-meta {{
            display: flex;
            gap: 20px;
            margin-top: 15px;
            font-size: 0.875rem;
            color: var(--text-muted);
        }}
        
        .app-section {{
            margin-bottom: 60px;
        }}
        
        .app-title {{
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .app-title::before {{
            content: '📦';
        }}
        
        .app-description {{
            color: var(--text-secondary);
            margin-bottom: 30px;
        }}
        
        .endpoint {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        
        .endpoint-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 20px;
            background: var(--bg-tertiary);
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
            margin-bottom: 20px;
        }}
        
        .endpoint-section {{
            margin-bottom: 25px;
        }}
        
        .endpoint-section-title {{
            font-size: 0.875rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            background: var(--bg-tertiary);
            padding: 12px 15px;
            border-radius: 8px;
        }}
        
        .info-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}
        
        .info-value {{
            font-size: 0.875rem;
            color: var(--text-primary);
        }}
        
        .fields-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }}
        
        .fields-table th {{
            text-align: left;
            padding: 12px 15px;
            background: var(--bg-tertiary);
            color: var(--text-secondary);
            font-weight: 600;
            border-bottom: 1px solid var(--border);
        }}
        
        .fields-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }}
        
        .fields-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .field-name {{
            font-family: 'JetBrains Mono', monospace;
            color: var(--cyan);
        }}
        
        .field-type {{
            color: var(--purple);
            font-size: 0.8rem;
        }}
        
        .required-badge {{
            font-size: 0.625rem;
            background: var(--danger);
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }}
        
        .optional-badge {{
            font-size: 0.625rem;
            background: var(--bg-tertiary);
            color: var(--text-muted);
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .code-block {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 15px;
            overflow-x: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            line-height: 1.6;
        }}
        
        .code-block pre {{
            margin: 0;
            color: var(--text-secondary);
        }}
        
        .json-key {{ color: var(--cyan); }}
        .json-string {{ color: var(--success); }}
        .json-number {{ color: var(--warning); }}
        .json-boolean {{ color: var(--purple); }}
        
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
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--text-muted);
        }}
        
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
        // Smooth scrolling for nav links
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
        
        // Highlight active section on scroll
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
        
        document.querySelectorAll('.endpoint').forEach(endpoint => {{
            observer.observe(endpoint);
        }});
    </script>
</body>
</html>'''
    
    def _generate_sidebar(self, apps: List[AppAPIInfo]) -> str:
        """Generate sidebar navigation HTML"""
        nav_items = []
        
        for app in apps:
            nav_items.append(f'''
            <div class="nav-group">
                <div class="nav-group-title">{app.app_label}</div>
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
        
        return f'''
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-title">{self.title}</div>
                <span class="sidebar-version">v{self.version}</span>
            </div>
            {''.join(nav_items)}
        </aside>
        '''
    
    def _generate_content(self, apps: List[AppAPIInfo]) -> str:
        """Generate main content HTML"""
        content = []
        
        for app in apps:
            endpoints_html = []
            
            for endpoint in app.endpoints:
                endpoint_html = self._generate_endpoint(app.app_name, endpoint)
                endpoints_html.append(endpoint_html)
            
            content.append(f'''
            <section class="app-section" id="app-{app.app_name}">
                <h2 class="app-title">{app.app_label}</h2>
                <p class="app-description">{app.description or f"API endpoints for {app.app_label}"}</p>
                {''.join(endpoints_html)}
            </section>
            ''')
        
        return ''.join(content)
    
    def _generate_endpoint(self, app_name: str, endpoint: EndpointInfo) -> str:
        """Generate HTML for a single endpoint"""
        endpoint_id = self._generate_id(app_name, endpoint.url)
        
        methods_html = ''.join([
            f'<span class="method-badge method-{m}">{m}</span>' 
            for m in endpoint.methods
        ])
        
        # Info grid
        info_items = []
        if endpoint.authentication:
            info_items.append(f'''
            <div class="info-item">
                <div class="info-label">🔐 Authentication</div>
                <div class="info-value">{', '.join(endpoint.authentication)}</div>
            </div>
            ''')
        if endpoint.permissions:
            info_items.append(f'''
            <div class="info-item">
                <div class="info-label">🛡️ Permissions</div>
                <div class="info-value">{', '.join(endpoint.permissions)}</div>
            </div>
            ''')
        if endpoint.path_params:
            info_items.append(f'''
            <div class="info-item">
                <div class="info-label">📍 Path Parameters</div>
                <div class="info-value">{', '.join([f'{{{p}}}' for p in endpoint.path_params])}</div>
            </div>
            ''')
        
        info_grid = f'<div class="info-grid">{"".join(info_items)}</div>' if info_items else ''
        
        # Query params table
        query_params_html = ''
        if endpoint.query_params:
            query_params_html = self._generate_fields_section(
                '📋 Query Parameters', endpoint.query_params
            )
        
        # Request body
        request_html = ''
        if endpoint.request_fields:
            request_html = self._generate_fields_section(
                '📤 Request Body', endpoint.request_fields, show_example=True
            )
        
        # Response
        response_html = ''
        if endpoint.response_fields:
            response_html = self._generate_fields_section(
                '📥 Response (200 OK)', endpoint.response_fields, show_example=True, is_response=True
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
                {query_params_html}
                {request_html}
                {response_html}
            </div>
        </div>
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
                
            badge = '<span class="required-badge">Required</span>' if field.required else '<span class="optional-badge">Optional</span>'
            
            desc_parts = []
            if field.help_text:
                desc_parts.append(field.help_text)
            if field.choices:
                desc_parts.append(f'Choices: {", ".join([str(c) for c in field.choices[:3]])}')
            description = ' | '.join(desc_parts) if desc_parts else '—'
            
            rows.append(f'''
            <tr>
                <td><span class="field-name">{field.name}</span></td>
                <td><span class="field-type">{field.field_type}</span></td>
                <td>{badge}</td>
                <td>{description}</td>
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
            highlighted_json = self._highlight_json(json_example)
            example_html = f'''
            <div style="margin-top: 15px;">
                <div class="code-block">
                    <pre>{highlighted_json}</pre>
                </div>
            </div>
            '''
        
        return f'''
        <div class="endpoint-section">
            <h4 class="endpoint-section-title">{title}</h4>
            {table_html}
            {example_html}
        </div>
        '''
    
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
            'date': '2024-01-15',
            'datetime': '2024-01-15T10:30:00Z',
            'time': '10:30:00',
            'uuid': '123e4567-e89b-12d3-a456-426614174000',
            'file': 'file.pdf',
            'image': 'image.jpg',
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
    
    def _highlight_json(self, json_str: str) -> str:
        """Add syntax highlighting to JSON"""
        import re
        
        # Highlight keys
        json_str = re.sub(r'"([^"]+)":', r'<span class="json-key">"\1"</span>:', json_str)
        # Highlight string values
        json_str = re.sub(r': "([^"]*)"', r': <span class="json-string">"\1"</span>', json_str)
        # Highlight numbers
        json_str = re.sub(r': (\d+\.?\d*)', r': <span class="json-number">\1</span>', json_str)
        # Highlight booleans
        json_str = re.sub(r': (true|false|null)', r': <span class="json-boolean">\1</span>', json_str)
        
        return json_str
    
    def _generate_id(self, app_name: str, url: str) -> str:
        """Generate a valid HTML ID from app name and URL"""
        import re
        id_str = f"{app_name}-{url}"
        id_str = re.sub(r'[^a-zA-Z0-9-]', '-', id_str)
        id_str = re.sub(r'-+', '-', id_str)
        return id_str.strip('-').lower()
