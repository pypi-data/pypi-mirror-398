"""
Django App Configuration for DRF API Documentation Generator
"""

from django.apps import AppConfig


class DrfApiDocGeneratorConfig(AppConfig):
    """
    Django app configuration for the API documentation generator.
    
    Add 'drf_api_doc_generator' to your INSTALLED_APPS to enable
    the generate_api_docs management command.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'drf_api_doc_generator'
    verbose_name = 'DRF API Documentation Generator'
    
    def ready(self):
        """Called when Django starts."""
        pass
