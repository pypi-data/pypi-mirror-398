"""
Core module for Salesforce Toolkit.

Provides the fundamental building blocks for Salesforce integration:
- Session management
- HTTP client for API requests
- CRUD operations on Salesforce objects
"""

from kinetic_core.core.session import SalesforceSession
from kinetic_core.core.client import SalesforceClient

__all__ = ["SalesforceSession", "SalesforceClient"]
