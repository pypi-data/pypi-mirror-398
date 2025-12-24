"""
Authentication module for Salesforce Toolkit.

Provides multiple authentication strategies for Salesforce:
- JWT Bearer Flow (recommended for production)
- OAuth 2.0 Password Flow (for development/testing)
"""

from kinetic_core.auth.jwt_auth import JWTAuthenticator
from kinetic_core.auth.oauth_auth import OAuthAuthenticator

__all__ = ["JWTAuthenticator", "OAuthAuthenticator"]
