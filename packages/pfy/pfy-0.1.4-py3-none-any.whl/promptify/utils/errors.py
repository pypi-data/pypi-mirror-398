"""
Custom exceptions for Promptify CLI
Provides clear, actionable error messages for users
"""


class PromptifyError(Exception):
    """Base exception for all Promptify errors"""
    
    def __init__(self, message: str, hint: str = None):
        self.message = message
        self.hint = hint
        super().__init__(self.message)
    
    def __str__(self):
        if self.hint:
            return f"{self.message}\n💡 Hint: {self.hint}"
        return self.message


class ValidationError(PromptifyError):
    """Raised when input validation fails"""
    pass


class ServiceError(PromptifyError):
    """Raised when the agent service fails"""
    pass


class ConfigurationError(PromptifyError):
    """Raised when configuration is invalid or missing"""
    pass


class APIError(PromptifyError):
    """Raised when external API calls fail"""
    
    def __init__(self, message: str, status_code: int = None, hint: str = None):
        self.status_code = status_code
        super().__init__(message, hint)
    
    def __str__(self):
        base = f"{self.message}"
        if self.status_code:
            base += f" (Status: {self.status_code})"
        if self.hint:
            base += f"\n💡 Hint: {self.hint}"
        return base


class FileOperationError(PromptifyError):
    """Raised when file read/write operations fail"""
    pass


# Convenience functions for common errors

def api_key_missing_error():
    """Standard error for missing API key"""
    return ConfigurationError(
        "GOOGLE_GENAI_API_KEY not found",
        hint="Create a .env file with GOOGLE_GENAI_API_KEY=your_key_here\n"
             "   Or set it as an environment variable\n"
             "   Get your key at: https://aistudio.google.com/app/apikey"
    )


def query_too_long_error(length: int, max_length: int = 5000):
    """Standard error for overly long queries"""
    return ValidationError(
        f"Query is too long ({length} characters)",
        hint=f"Maximum length is {max_length} characters. Consider breaking it into smaller parts."
    )


def file_not_found_error(file_path: str):
    """Standard error for missing files"""
    return FileOperationError(
        f"File not found: {file_path}",
        hint="Check the file path and ensure the file exists"
    )


def rate_limit_error(retry_after: int = None):
    """Standard error for API rate limiting"""
    hint = "You've hit the API rate limit."
    if retry_after:
        hint += f" Try again in {retry_after} seconds."
    else:
        hint += " Wait a moment and try again."
    
    return APIError(
        "API rate limit exceeded",
        status_code=429,
        hint=hint
    )


def network_error():
    """Standard error for network issues"""
    return APIError(
        "Network error: Could not reach the API",
        hint="Check your internet connection and try again"
    )
