"""
ForgeVault SDK - Prompt Management for Production AI Applications

Copyright (c) 2025 ForgeVault. All Rights Reserved.
This is proprietary software. See LICENSE file for terms.
"""

from forgevault.client import Forge, _VERSION
from forgevault.prompt import Prompt
from forgevault.exceptions import (
    ForgeVaultError,
    AuthenticationError,
    PromptNotFoundError,
    RenderError,
    ExecutionError,
    RateLimitError,
    ConnectionError
)

__version__ = _VERSION
__author__ = "ForgeVault"
__license__ = "Proprietary"

__all__ = [
    "Forge",
    "Prompt",
    "ForgeVaultError",
    "AuthenticationError",
    "PromptNotFoundError",
    "RenderError",
    "ExecutionError",
    "RateLimitError",
    "ConnectionError"
]
