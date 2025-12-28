"""EShopBox Python SDK - A comprehensive package for EShopBox shipping APIs"""

from eshopbox.__version__ import __version__, __author__, __email__
from eshopbox.client import EShopBoxSDK
from eshopbox.exceptions import (
    EShopBoxException,
    AuthenticationError,
    APIError,
    ValidationError,
    RateLimitError,
    NotFoundError
)

__all__ = [
    'EShopBoxSDK',
    'EShopBoxException',
    'AuthenticationError',
    'APIError',
    'ValidationError',
    'RateLimitError',
    'NotFoundError',
    '__version__'
]