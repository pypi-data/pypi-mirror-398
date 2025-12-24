"""Custom exceptions for InstaVM operations"""

class InstaVMError(Exception):
    """Base exception for InstaVM operations"""
    pass

class AuthenticationError(InstaVMError):
    """Authentication failed"""
    pass

class SessionError(InstaVMError):
    """Session-related errors"""
    pass

class ExecutionError(InstaVMError):
    """Code execution failed"""
    pass

class NetworkError(InstaVMError):
    """Network connectivity issues"""
    pass

class RateLimitError(InstaVMError):
    """API rate limit exceeded"""
    pass

# Browser-specific exceptions
class BrowserError(InstaVMError):
    """Base exception for browser automation errors"""
    pass

class BrowserSessionError(BrowserError):
    """Browser session management errors"""
    pass

class BrowserInteractionError(BrowserError):
    """Browser interaction errors (click, type, etc.)"""
    pass

class BrowserTimeoutError(BrowserError):
    """Browser timeout errors"""
    pass

class BrowserNavigationError(BrowserError):
    """Browser navigation errors"""
    pass

class ElementNotFoundError(BrowserInteractionError):
    """Element not found for browser interaction"""
    pass

class QuotaExceededError(InstaVMError):
    """API quota exceeded"""
    pass

class UnsupportedOperationError(InstaVMError):
    """Operation not supported in local mode"""
    pass