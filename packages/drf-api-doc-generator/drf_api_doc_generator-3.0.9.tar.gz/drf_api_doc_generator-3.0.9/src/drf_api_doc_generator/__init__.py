"""
DRF API Documentation Generator
===============================

Auto-generate production-quality API documentation for Django REST Framework.

Generate beautiful PDF, HTML, and OpenAPI JSON documentation with a single command:

    python manage.py generate_api_docs <app_name>

Features:
    - PDF documentation with cover page, TOC, and professional styling
    - HTML documentation with dark theme and interactive sidebar
    - OpenAPI 3.0 JSON for Swagger UI and Postman compatibility
    - Auto-detection of endpoints, serializers, auth, and permissions
    - Customizable via Django settings

Quick Start:
    1. Add 'drf_api_doc_generator' to INSTALLED_APPS
    2. Run: python manage.py generate_api_docs <your_app>
    3. Find docs in ./api_docs/ directory

For more information, visit:
    https://github.com/yourusername/drf-api-doc-generator

"""

__version__ = "1.0.0"
__author__ = "Ashiq"
__license__ = "MIT"

default_app_config = 'drf_api_doc_generator.apps.DrfApiDocGeneratorConfig'
