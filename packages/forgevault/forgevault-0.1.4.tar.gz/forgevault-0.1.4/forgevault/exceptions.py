"""
ForgeVault SDK Exceptions

Copyright (c) 2025 ForgeVault. All Rights Reserved.
"""


class ForgeVaultError(Exception):
    """Base exception for ForgeVault SDK"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(ForgeVaultError):
    """Raised when API key is invalid or missing"""
    
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, error_code="AUTH_ERROR")


class PromptNotFoundError(ForgeVaultError):
    """Raised when a prompt is not found"""
    
    def __init__(self, prompt_identifier: str):
        super().__init__(
            f"Prompt not found: {prompt_identifier}",
            error_code="NOT_FOUND",
            details={"prompt": prompt_identifier}
        )


class RenderError(ForgeVaultError):
    """Raised when prompt rendering fails"""
    
    def __init__(self, message: str, missing_variables: list = None):
        super().__init__(
            message,
            error_code="RENDER_ERROR",
            details={"missing_variables": missing_variables or []}
        )


class ExecutionError(ForgeVaultError):
    """Raised when prompt execution fails"""
    
    def __init__(self, message: str, model: str = None):
        super().__init__(
            message,
            error_code="EXECUTION_ERROR",
            details={"model": model}
        )


class RateLimitError(ForgeVaultError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, retry_after: int = None):
        super().__init__(
            "Rate limit exceeded",
            error_code="RATE_LIMIT",
            details={"retry_after": retry_after}
        )


class ConnectionError(ForgeVaultError):
    """Raised when connection to ForgeVault API fails"""
    
    def __init__(self, message: str = "Failed to connect to ForgeVault API"):
        super().__init__(message, error_code="CONNECTION_ERROR")

