"""
Django Management Command: generate_api_docs

Generates production-quality API documentation for Django REST Framework apps.

Usage:
    python manage.py generate_api_docs <app_name>
    python manage.py generate_api_docs <app1> <app2> ...
    python manage.py generate_api_docs --all
    python manage.py generate_api_docs auth --format pdf --output ./docs/

Examples:
    # Generate PDF documentation for the 'auth' app
    python manage.py generate_api_docs auth

    # Generate all formats (PDF, HTML, JSON) for multiple apps
    python manage.py generate_api_docs auth users --format all

    # Generate docs for all apps with custom title
    python manage.py generate_api_docs --all --title "My API" --api-version "2.0.0"

    # Generate and automatically open the file
    python manage.py generate_api_docs auth --open
"""

import os
import sys
import webbrowser
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from drf_api_doc_generator.core.parser import APIParser
from drf_api_doc_generator.core.pdf_generator import PDFGenerator
from drf_api_doc_generator.core.html_generator import HTMLGenerator
from drf_api_doc_generator.core.json_generator import JSONGenerator


class Command(BaseCommand):
    """
    Generate API documentation for Django REST Framework applications.
    
    This command automatically discovers API endpoints, serializers,
    authentication classes, and permissions from your DRF views and
    generates professional documentation in PDF, HTML, or JSON format.
    """
    
    help = 'Generate API documentation for Django REST Framework apps'
    
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
    
    def handle(self, *args, **options):
        """Main command handler"""
        
        # Use Django's built-in verbosity (0=minimal, 1=normal, 2=verbose, 3=very verbose)
        self.verbose = options.get('verbosity', 1) >= 2
        
        # Print header (using ASCII-compatible characters for Windows)
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('+' + '=' * 58 + '+'))
        self.stdout.write(self.style.SUCCESS('|' + ' DRF API Documentation Generator '.center(58) + '|'))
        self.stdout.write(self.style.SUCCESS('+' + '=' * 58 + '+'))
        self.stdout.write('')
        
        # Get app names
        app_names = options.get('apps', [])
        all_apps = options.get('all_apps', False)
        
        if not app_names and not all_apps:
            raise CommandError(
                'Please specify app names or use --all flag.\n'
                'Usage: python manage.py generate_api_docs <app_name> [<app_name> ...]\n'
                '       python manage.py generate_api_docs --all'
            )
        
        if all_apps:
            app_names = None  # Parser will detect all apps
            self.stdout.write(self.style.HTTP_INFO('[*] Scanning all installed apps...'))
        else:
            self.stdout.write(self.style.HTTP_INFO(f'[*] Scanning apps: {", ".join(app_names)}'))
        
        # Get configuration
        config = self._get_config(options)
        
        # Parse APIs
        self.stdout.write(self.style.HTTP_INFO('[*] Parsing API endpoints...'))
        
        try:
            parser = APIParser(app_names)
            parsed_apps = parser.parse_all()
        except ImportError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Error parsing APIs: {e}')
        
        if not parsed_apps:
            self.stdout.write(self.style.WARNING(
                '\n[!] No API endpoints found!\n'
                'Make sure your apps have:\n'
                '  - REST Framework views (APIView, ViewSet)\n'
                '  - URL patterns connected to those views\n'
            ))
            return
        
        # Count endpoints
        total_endpoints = sum(len(app.endpoints) for app in parsed_apps)
        self.stdout.write(self.style.SUCCESS(
            f'[+] Found {total_endpoints} endpoints in {len(parsed_apps)} app(s)'
        ))
        
        if self.verbose:
            for app in parsed_apps:
                self.stdout.write(f'\n  [App] {app.app_label}:')
                for endpoint in app.endpoints:
                    methods = ', '.join(endpoint.methods)
                    self.stdout.write(f'     [{methods}] {endpoint.url}')
        
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
                    file_path = generator.generate(parsed_apps, output_path)
                    generated_files.append(('PDF', file_path))
                    
                elif fmt == 'html':
                    output_path = os.path.join(output_dir, f'api_docs_{timestamp}.html')
                    generator = HTMLGenerator(config)
                    file_path = generator.generate(parsed_apps, output_path)
                    generated_files.append(('HTML', file_path))
                    
                elif fmt == 'json':
                    output_path = os.path.join(output_dir, f'api_docs_{timestamp}.json')
                    generator = JSONGenerator(config)
                    file_path = generator.generate(parsed_apps, output_path)
                    generated_files.append(('JSON/OpenAPI', file_path))
                    
            except ImportError as e:
                self.stdout.write(self.style.ERROR(f'[X] Cannot generate {fmt.upper()}: {e}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'[X] Error generating {fmt.upper()}: {e}'))
        
        # Print results
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('[+] Documentation generated successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        for fmt, path in generated_files:
            file_size = os.path.getsize(path)
            size_str = self._format_file_size(file_size)
            self.stdout.write(f'\n[File] {fmt} ({size_str}):')
            self.stdout.write(self.style.HTTP_REDIRECT(f'   {path}'))
        
        self.stdout.write('')
        
        # Open file if requested
        if options.get('open_file') and generated_files:
            primary_file = generated_files[0][1]
            self.stdout.write(self.style.HTTP_INFO(f'[*] Opening {primary_file}...'))
            webbrowser.open(f'file://{primary_file}')
        
        # Print summary
        self.stdout.write(self.style.SUCCESS('\n[Summary]'))
        self.stdout.write(f'   Apps documented: {len(parsed_apps)}')
        self.stdout.write(f'   Total endpoints: {total_endpoints}')
        self.stdout.write(f'   Files generated: {len(generated_files)}')
        self.stdout.write('')
    
    def _get_config(self, options) -> dict:
        """Get configuration from settings and command options"""
        
        # Default config
        config = {
            'TITLE': 'API Documentation',
            'VERSION': '1.0.0',
            'DESCRIPTION': 'Complete API Reference for Developers',
            'CONTACT_EMAIL': '',
            'LOGO_PATH': None,
            'THEME_COLOR': '#2563eb',
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
