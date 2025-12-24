"""
Salesforce Toolkit - A comprehensive Python library for Salesforce integration.

This toolkit provides a flexible, configuration-driven framework for:
- Authentication (JWT Bearer Flow, OAuth Password Flow)
- CRUD operations on any Salesforce object
- Field mapping and data transformation
- ETL pipelines for data synchronization
- Comprehensive logging and error handling

Author: Antonio Trento
License: MIT
"""

__version__ = "1.1.1"
"""
Salesforce Toolkit - DEPRECATED
"""

import warnings

DEPRECATION_MSG = (
    "The 'salesforce-toolkit' package is deprecated and unsupported due to trademark policy. "
    "Please switch to 'kinetic-core'. "
    "Run: pip install kinetic-core"
)

# Raise a RuntimeError to prevent usage
raise RuntimeError(DEPRECATION_MSG)
