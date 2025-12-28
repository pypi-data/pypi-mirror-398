"""
Django Management Command: generate_api_docs

Generates production-quality API documentation for Django REST Framework apps
and WebSocket consumers.

Usage:
    python manage.py generate_api_docs <app_name>
    python manage.py generate_api_docs <app1> <app2> ...
    python manage.py generate_api_docs --all
    python manage.py generate_api_docs auth --format pdf --output ./docs/
    
WebSocket Documentation:
    python manage.py generate_api_docs --websocket path/to/consumers.py
    python manage.py generate_api_docs auth --websocket chat/consumers/dm_consumer.py
"""

import os
import sys
import webbrowser
import zipfile
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps

from api_docs_generator.core.parser import APIParser
from api_docs_generator.core.pdf_generator import PDFGenerator
from api_docs_generator.core.html_generator import HTMLGenerator
from api_docs_generator.core.json_generator import JSONGenerator
from api_docs_generator.core.websocket_parser import WebSocketParser


class Command(BaseCommand):
    help = 'Generate API documentation for Django REST Framework apps and WebSocket consumers'
    
    def add_arguments(self, parser):
        # Positional arguments - app names
        parser.add_argument(
            'apps',
            nargs='*',
            type=str,
            help='App names to generate documentation for'
        )
        
        # Optional: Generate for all apps
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all_apps',
            help='Generate documentation for all installed apps'
        )
        
        # WebSocket consumer files
        parser.add_argument(
            '--websocket', '-ws',
            nargs='*',
            type=str,
            dest='websocket_files',
            help='Path(s) to WebSocket consumer files to document'
        )
        
        # WebSocket consumer code (direct input)
        parser.add_argument(
            '--websocket-code',
            type=str,
            dest='websocket_code',
            help='WebSocket consumer code as string (for programmatic use)'
        )
        
        # Output format
        parser.add_argument(
            '--format', '-f',
            type=str,
            choices=['pdf', 'html', 'json', 'all'],
            default='pdf',
            help='Output format (default: pdf)'
        )
        
        # Output directory
        parser.add_argument(
            '--output', '-o',
            type=str,
            default='./api_docs/',
            help='Output directory for generated files (default: ./api_docs/)'
        )
        
        # Open after generation
        parser.add_argument(
            '--open',
            action='store_true',
            dest='open_file',
            help='Open the generated file after creation'
        )
        
        # Configuration options
        parser.add_argument(
            '--title',
            type=str,
            help='Custom title for the documentation'
        )
        
        parser.add_argument(
            '--api-version',
            type=str,
            dest='api_version',
            help='API version'
        )
        
        parser.add_argument(
            '--description',
            type=str,
            help='API description'
        )
        
        # WebSocket specific options
        parser.add_argument(
            '--ws-base-url',
            type=str,
            dest='ws_base_url',
            default='ws://domain',
            help='WebSocket base URL (default: ws://domain)'
        )
        
        # ZIP option for sharing with frontend developers
        parser.add_argument(
            '--zip',
            action='store_true',
            dest='create_zip',
            help='Create a ZIP file containing the documentation (useful for sharing)'
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        self.verbose = options.get('verbosity', 1) >= 2
        
        # Print header
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('+' + '=' * 62 + '+'))
        self.stdout.write(self.style.SUCCESS('|' + ' Django REST API & WebSocket Documentation Generator '.center(62) + '|'))
        self.stdout.write(self.style.SUCCESS('+' + '=' * 62 + '+'))
        self.stdout.write('')
        
        # Get app names
        app_names = options.get('apps', [])
        
        # Check for magic command "complete-project-zip-html"
        if app_names and 'complete-project-zip-html' in app_names:
            self.stdout.write(self.style.SUCCESS('[*] Magic Command Detected: Generating Complete Project Documentation...'))
            
            # Override options for complete project generation
            options['all_apps'] = True
            options['format'] = 'html'
            options['create_zip'] = True
            
            # Auto-discover WebSocket consumer files
            discovered_ws = self._discover_consumer_files()
            if discovered_ws:
                options['websocket_files'] = discovered_ws
                self.stdout.write(self.style.SUCCESS(f'    [+] Auto-discovered {len(discovered_ws)} consumer files'))
            
            # Clear explicit app names (since we used a magic string)
            app_names = []
            
        all_apps = options.get('all_apps', False)
        websocket_files = options.get('websocket_files', [])
        websocket_code = options.get('websocket_code', '')
        
        # Check if we have something to document
        if not app_names and not all_apps and not websocket_files and not websocket_code:
            raise CommandError(
                'Please specify app names, use --all flag, or provide --websocket files.\n'
                'Usage: python manage.py generate_api_docs <app_name> [<app_name> ...]\n'
                '       python manage.py generate_api_docs --all\n'
                '       python manage.py generate_api_docs --websocket path/to/consumers.py'
            )
        
        # Get configuration
        config = self._get_config(options)
        
        parsed_apps = []
        websocket_apps = []
        
        # Parse REST APIs
        if app_names or all_apps:
            if all_apps:
                app_names = None
                self.stdout.write(self.style.HTTP_INFO('[*] Scanning all installed apps...'))
            else:
                self.stdout.write(self.style.HTTP_INFO(f'[*] Scanning apps: {", ".join(app_names)}'))
            
            self.stdout.write(self.style.HTTP_INFO('[*] Parsing REST API endpoints...'))
            
            try:
                parser = APIParser(app_names)
                parsed_apps = parser.parse_all()
            except ImportError as e:
                raise CommandError(str(e))
            except Exception as e:
                raise CommandError(f'Error parsing APIs: {e}')
        
        # Parse WebSocket consumers
        if websocket_files or websocket_code:
            self.stdout.write(self.style.HTTP_INFO('[*] Parsing WebSocket consumers...'))
            
            ws_parser = WebSocketParser(config=config)
            
            # Parse from files
            if websocket_files:
                for file_path in websocket_files:
                    if os.path.exists(file_path):
                        try:
                            ws_app = ws_parser.parse_from_file(file_path)
                            self.stdout.write(self.style.SUCCESS(
                                f'    [+] Parsed: {file_path} ({len(ws_app.endpoints)} endpoints)'
                            ))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f'    [!] Could not parse {file_path}: {e}'
                            ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'    [!] File not found: {file_path}'
                        ))
            
            # Parse from code string
            if websocket_code:
                try:
                    ws_app = ws_parser.parse_from_content(websocket_code, "direct_input")
                    self.stdout.write(self.style.SUCCESS(
                        f'    [+] Parsed WebSocket code ({len(ws_app.endpoints)} endpoints)'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'    [!] Could not parse WebSocket code: {e}'
                    ))
            
            websocket_apps = ws_parser.parsed_apps
        
        # Check if we found anything
        if not parsed_apps and not websocket_apps:
            self.stdout.write(self.style.WARNING(
                '\n[!] No API endpoints or WebSocket consumers found!\n'
                'Make sure your apps have:\n'
                '  - REST Framework views (APIView, ViewSet)\n'
                '  - URL patterns connected to those views\n'
                '  - Or provide valid WebSocket consumer files\n'
            ))
            return
        
        # Count endpoints
        total_rest_endpoints = sum(len(app.endpoints) for app in parsed_apps)
        total_ws_endpoints = sum(len(app.endpoints) for app in websocket_apps)
        
        if parsed_apps:
            self.stdout.write(self.style.SUCCESS(
                f'[+] Found {total_rest_endpoints} REST endpoints in {len(parsed_apps)} app(s)'
            ))
        
        if websocket_apps:
            self.stdout.write(self.style.SUCCESS(
                f'[+] Found {total_ws_endpoints} WebSocket endpoints in {len(websocket_apps)} app(s)'
            ))
        
        if self.verbose:
            for app in parsed_apps:
                self.stdout.write(f'\n  [REST App] {app.app_label}:')
                for endpoint in app.endpoints:
                    methods = ', '.join(endpoint.methods)
                    self.stdout.write(f'     [{methods}] {endpoint.url}')
            
            for ws_app in websocket_apps:
                self.stdout.write(f'\n  [WebSocket App] {ws_app.app_label}:')
                for endpoint in ws_app.endpoints:
                    self.stdout.write(f'     [WS] {endpoint.url} - {endpoint.name}')
                    for action in endpoint.actions:
                        self.stdout.write(f'         -> {action.name}')
        
        # Get output format and directory
        output_format = options.get('format', 'pdf')
        output_dir = options.get('output', './api_docs/')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        generated_files = []
        
        # Generate documentation
        self.stdout.write(self.style.HTTP_INFO(f'\n[*] Generating {output_format.upper()} documentation...'))
        
        formats_to_generate = ['pdf', 'html', 'json'] if output_format == 'all' else [output_format]
        
        for fmt in formats_to_generate:
            try:
                if fmt == 'pdf':
                    output_path = os.path.join(output_dir, f'api_docs_{timestamp}.pdf')
                    generator = PDFGenerator(config)
                    file_path = generator.generate(parsed_apps, output_path, websocket_apps)
                    generated_files.append(('PDF', file_path))
                    
                elif fmt == 'html':
                    output_path = os.path.join(output_dir, f'api_docs_{timestamp}.html')
                    generator = HTMLGenerator(config)
                    file_path = generator.generate(parsed_apps, output_path, websocket_apps)
                    generated_files.append(('HTML', file_path))
                    
                elif fmt == 'json':
                    output_path = os.path.join(output_dir, f'api_docs_{timestamp}.json')
                    generator = JSONGenerator(config)
                    # JSON generator needs update too - for now just pass REST APIs
                    file_path = generator.generate(parsed_apps, output_path)
                    generated_files.append(('JSON/OpenAPI', file_path))
                    
            except ImportError as e:
                self.stdout.write(self.style.ERROR(f'[X] Cannot generate {fmt.upper()}: {e}'))
            except Exception as e:
                import traceback
                if self.verbose:
                    traceback.print_exc()
                self.stdout.write(self.style.ERROR(f'[X] Error generating {fmt.upper()}: {e}'))
        
        # Print results
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 64))
        self.stdout.write(self.style.SUCCESS('[+] Documentation generated successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 64))
        
        for fmt, path in generated_files:
            file_size = os.path.getsize(path)
            size_str = self._format_file_size(file_size)
            self.stdout.write(f'\n[File] {fmt} ({size_str}):')
            self.stdout.write(self.style.HTTP_REDIRECT(f'   {path}'))
        
        self.stdout.write('')
        
        # Create ZIP if requested
        if options.get('create_zip') and generated_files:
            zip_path = self._create_zip_file(generated_files, output_dir, timestamp, config)
            if zip_path:
                zip_size = os.path.getsize(zip_path)
                size_str = self._format_file_size(zip_size)
                self.stdout.write(f'\n[ZIP] Documentation Package ({size_str}):')
                self.stdout.write(self.style.SUCCESS(f'   {zip_path}'))
                self.stdout.write(self.style.HTTP_INFO('   -> Share this with frontend developers!'))
        
        # Open file if requested
        if options.get('open_file') and generated_files:
            primary_file = generated_files[0][1]
            self.stdout.write(self.style.HTTP_INFO(f'\n[*] Opening {primary_file}...'))
            webbrowser.open(f'file://{primary_file}')
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n[Summary]'))
        if parsed_apps:
            self.stdout.write(f'   REST APIs documented: {len(parsed_apps)} apps, {total_rest_endpoints} endpoints')
        if websocket_apps:
            self.stdout.write(f'   WebSocket APIs documented: {len(websocket_apps)} apps, {total_ws_endpoints} endpoints')
        self.stdout.write(f'   Files generated: {len(generated_files)}')
        if options.get('create_zip'):
            self.stdout.write(f'   ZIP package: Created [OK]')
        self.stdout.write('')
    
    
    def _discover_consumer_files(self) -> list:
        """
        Auto-discover consumer files in all installed apps.
        Looks for:
        - consumers.py (top level in app)
        - consumers/ directory (files inside)
        - Any file ending with _consumers.py or consumers.py
        """
        discovered_files = []
        
        for app_config in apps.get_app_configs():
            app_path = app_config.path
            
            # 1. Check for standard consumers.py
            std_consumers = os.path.join(app_path, 'consumers.py')
            if os.path.exists(std_consumers):
                discovered_files.append(std_consumers)
                
            # 2. Check for recursive search in the app directory
            for root, dirs, files in os.walk(app_path):
                # Skip __pycache__ and migrations
                if '__pycache__' in dirs:
                    dirs.remove('__pycache__')
                if 'migrations' in dirs:
                    dirs.remove('migrations')
                    
                for file in files:
                    # Match consumers.py, consumer.py, or any similar variation
                    if (file == 'consumers.py' and os.path.join(root, file) != std_consumers) or \
                       (file == 'consumer.py') or \
                       (file.endswith('_consumers.py') or file.endswith('_consumer.py')) or \
                       ('consumer' in file and file.endswith('.py')):
                        
                        full_path = os.path.join(root, file)
                        # Avoid duplicates
                        if full_path not in discovered_files:
                            discovered_files.append(full_path)
                            
        return discovered_files

    def _get_config(self, options) -> dict:
        """Get configuration from settings and command options"""
        
        # Default config
        config = {
            'TITLE': 'API Documentation',
            'VERSION': '3.0.5',
            'DESCRIPTION': 'Complete API & WebSocket Reference for Developers',
            'CONTACT_EMAIL': '',
            'LOGO_PATH': None,
            'THEME_COLOR': '#2563eb',
            'WS_BASE_URL': options.get('ws_base_url', 'ws://domain'),
        }
        
        # Override with settings
        if hasattr(settings, 'API_DOCS_CONFIG'):
            config.update(settings.API_DOCS_CONFIG)
        
        # Override with command line options
        if options.get('title'):
            config['TITLE'] = options['title']
        if options.get('api_version'):
            config['VERSION'] = options['api_version']
        if options.get('description'):
            config['DESCRIPTION'] = options['description']
        
        return config
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'
    
    def _create_zip_file(self, generated_files: list, output_dir: str, 
                         timestamp: str, config: dict) -> str:
        """
        Create a ZIP file containing all generated documentation.
        Useful for sharing with frontend developers.
        
        Args:
            generated_files: List of (format_name, file_path) tuples
            output_dir: Output directory path
            timestamp: Timestamp string for filename
            config: Configuration dictionary
            
        Returns:
            Path to the created ZIP file
        """
        try:
            # Create ZIP filename
            title_slug = config.get('TITLE', 'api_docs').lower()
            title_slug = ''.join(c if c.isalnum() else '_' for c in title_slug)
            zip_filename = f'{title_slug}_{timestamp}.zip'
            zip_path = os.path.join(output_dir, zip_filename)
            
            # Create ZIP file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add a README file
                readme_content = f"""# {config.get('TITLE', 'API Documentation')}

Version: {config.get('VERSION', '1.0.0')}
Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}

## Contents

This ZIP contains the API documentation files:

"""
                for fmt, fpath in generated_files:
                    fname = os.path.basename(fpath)
                    readme_content += f"- **{fname}** - {fmt} format\n"
                
                readme_content += """

## How to Use

### HTML Documentation
1. Extract the ZIP file
2. Open the `.html` file in any web browser
3. No server required - works offline!

### PDF Documentation
1. Open the `.pdf` file with any PDF reader
2. Great for printing or offline reference

### JSON (OpenAPI)
1. Import the `.json` file into:
   - Swagger UI
   - Postman
   - Insomnia
   - Any OpenAPI-compatible tool

---
Generated by DRF API & WebSocket Documentation Generator
"""
                zf.writestr('README.md', readme_content)
                
                # Add all generated files
                for fmt, file_path in generated_files:
                    if os.path.exists(file_path):
                        arcname = os.path.basename(file_path)
                        zf.write(file_path, arcname)
            
            return os.path.abspath(zip_path)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'[X] Error creating ZIP: {e}'))
            return None
