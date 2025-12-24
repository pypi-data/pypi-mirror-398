"""
Custom exceptions for the Arca SDK
"""

from typing import Optional


class ArcaError(Exception):
    """Base exception for all Arca SDK errors"""
    pass


class ArcaAPIError(ArcaError):
    """Raised when the API returns an error response"""
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        technical_details: Optional[str] = None,
        problematic_query: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details
        self.suggestion = suggestion
        self.technical_details = technical_details
        self.problematic_query = problematic_query
        
        error_parts = [f"API Error (status {status_code}): {message}" if status_code else message]
        
        if details:
            error_parts.append(f"\nDetails: {details}")
        if suggestion:
            error_parts.append(f"\nSuggestion: {suggestion}")
        if problematic_query:
            error_parts.append(f"\nProblematic Query: {problematic_query}")
        if technical_details:
            error_parts.append(f"\nTechnical Details: {technical_details}")
            
        super().__init__("".join(error_parts))


class ArcaAuthError(ArcaError):
    """Raised when authentication fails"""
    pass


class ArcaValidationError(ArcaError):
    """Raised when request validation fails"""
    pass
