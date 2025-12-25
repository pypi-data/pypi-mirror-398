"""
Safe mode parameters
"""

from looker_sdk.error import SDKError

SAFE_MODE_MAX_ERRORS = 3
SAFE_MODE_EXCEPTIONS = (SDKError,)
