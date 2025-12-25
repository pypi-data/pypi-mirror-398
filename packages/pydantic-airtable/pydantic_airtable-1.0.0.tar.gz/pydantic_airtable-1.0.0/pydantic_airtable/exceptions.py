"""
Custom exceptions for the Pydantic Airtable library
"""


class AirtableError(Exception):
    """Base exception for all Airtable related errors"""
    pass


class RecordNotFoundError(AirtableError):
    """Raised when a requested record is not found in Airtable"""
    pass


class ValidationError(AirtableError):
    """Raised when data validation fails"""
    pass


class APIError(AirtableError):
    """Raised when Airtable API returns an error"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class ConfigurationError(AirtableError):
    """Raised when there's an issue with configuration"""
    pass

