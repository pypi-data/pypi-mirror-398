"""
Template management for PTR elements.

This module provides a template registry system for storing and retrieving
reusable PTR element templates. Templates can be organized into groups,
loaded from files, and displayed in Jupyter notebooks.

The main way to access templates is through the service registry:
    >>> from ptr_editor.services.quick_access import get_template_register
    >>> register = get_template_register()
    >>> template = register.get("observation_block")
"""

from .html import generate_notebook_html
from .register import TemplateRegister
from .template import Template

__all__ = [
    "Template",
    "TemplateRegister",
    "generate_notebook_html",
]
