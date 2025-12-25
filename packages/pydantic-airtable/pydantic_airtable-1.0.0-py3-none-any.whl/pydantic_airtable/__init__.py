"""
Pydantic Airtable - A streamlined library for managing Airtable data using Pydantic objects

This library provides a clean, intuitive API for integrating Pydantic models with Airtable,
with smart field detection and minimal configuration required.

Quick Start:
    from pydantic_airtable import airtable_model, configure_from_env
    from pydantic import BaseModel
    
    # Configure from environment
    configure_from_env()
    
    # Define model with decorator
    @airtable_model(table_name="Users")
    class User(BaseModel):
        name: str
        email: str  # Automatically detected as EMAIL field type
        age: Optional[int] = None
    
    # Create and use
    user = User.create(name="Alice", email="alice@example.com", age=28)
    all_users = User.all()
"""

# Core API
from .models import AirtableModel, airtable_model
from .config import AirtableConfig, configure_from_env, set_global_config, get_global_config
from .field_types import airtable_field, FieldTypeResolver
from .fields import AirtableFieldType, AirtableField
from .manager import AirtableManager
from .exceptions import (
    AirtableError, 
    RecordNotFoundError, 
    ValidationError, 
    APIError, 
    ConfigurationError
)

# Internal components (for advanced usage)
from .http_client import BaseHTTPClient
from .client import AirtableClient
from .base_manager import BaseManager
from .table_manager import TableManager

__version__ = "1.0.0"

# Primary exports
__all__ = [
    # Main decorator and model
    "airtable_model",
    "AirtableModel", 
    
    # Configuration  
    "AirtableConfig",
    "configure_from_env",
    "set_global_config",
    "get_global_config",
    
    # Field utilities
    "airtable_field",
    "AirtableField",
    "AirtableFieldType",
    "FieldTypeResolver",
    
    # Manager
    "AirtableManager",
    
    # Exceptions
    "AirtableError",
    "RecordNotFoundError", 
    "ValidationError",
    "APIError",
    "ConfigurationError",
    
    # Internal components
    "BaseHTTPClient",
    "AirtableClient",
    "BaseManager",
    "TableManager",
]

# Convenience aliases for most common use cases
configure = configure_from_env
model = airtable_model
field = airtable_field

# Version info
VERSION = __version__
MAJOR, MINOR, PATCH = __version__.split('.')
VERSION_INFO = (int(MAJOR), int(MINOR), int(PATCH))

def get_version() -> str:
    """Get the current version string"""
    return __version__

def get_version_info() -> tuple:
    """Get version as tuple of integers"""
    return VERSION_INFO