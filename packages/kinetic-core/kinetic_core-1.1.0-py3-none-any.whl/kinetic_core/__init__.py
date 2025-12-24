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

__version__ = "1.1.0"
__author__ = "Antonio Trento"

from kinetic_core.auth.jwt_auth import JWTAuthenticator
from kinetic_core.auth.oauth_auth import OAuthAuthenticator
from kinetic_core.core.session import SalesforceSession
from kinetic_core.core.client import SalesforceClient
from kinetic_core.mapping.field_mapper import FieldMapper
from kinetic_core.pipeline.sync_pipeline import SyncPipeline, SyncMode

__all__ = [
    "JWTAuthenticator",
    "OAuthAuthenticator",
    "SalesforceSession",
    "SalesforceClient",
    "FieldMapper",
    "SyncPipeline",
    "SyncMode",
]
