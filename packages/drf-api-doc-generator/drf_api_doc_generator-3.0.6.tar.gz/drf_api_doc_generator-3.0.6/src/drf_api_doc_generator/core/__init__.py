"""
Core modules for API Documentation Generator

This module provides the main functionality for parsing Django REST Framework
applications and generating documentation in various formats.

Classes:
    APIParser: Parses DRF views, serializers, and URL patterns
    PDFGenerator: Generates professional PDF documentation
    HTMLGenerator: Generates interactive HTML documentation
    JSONGenerator: Generates OpenAPI 3.0 JSON specification

Example:
    from drf_api_doc_generator.core import APIParser, PDFGenerator
    
    parser = APIParser(['myapp'])
    apps = parser.parse_all()
    
    generator = PDFGenerator({'TITLE': 'My API Docs'})
    generator.generate(apps, 'output.pdf')
"""

from .parser import APIParser
from .pdf_generator import PDFGenerator
from .html_generator import HTMLGenerator
from .json_generator import JSONGenerator

__all__ = ['APIParser', 'PDFGenerator', 'HTMLGenerator', 'JSONGenerator']
