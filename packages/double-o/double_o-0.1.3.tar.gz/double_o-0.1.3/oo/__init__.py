"""
Double-O: A Python library for secret management and API proxy calls.

Simple usage:
    >>> import oo
    >>> secret = oo.get_secret("YOUR_TOKEN")
    >>> result = oo.proxy("v1/chat/completions", token="TOKEN", payload={...})

Environment variables:
    >>> import oo
    >>> env = oo.get_env("YOUR_VIRTUAL_ENV_TOKEN")  # Returns dict of secrets
    >>> oo.load_env("YOUR_VIRTUAL_ENV_TOKEN")  # Sets os.environ automatically

Advanced usage with Client:
    >>> from oo import Client
    >>> with Client(base_url="http://localhost:3001") as client:
    ...     secret = client.get_secret("TOKEN")
    ...     result = client.proxy("v1/chat/completions", "TOKEN", payload={...})
"""

from .client import (
    Client,
    get_secret,
    proxy,
    chat,
    get_env,
    load_env,
)
from .exceptions import (
    DoubleOError,
    SecretError,
    ProxyError,
    AuthenticationError,
    EnvError,
)

__version__ = "0.1.0"
__author__ = "Double-O Contributors"
__all__ = [
    # Main client
    "Client",
    # Convenience functions
    "get_secret",
    "proxy",
    "chat",
    "get_env",
    "load_env",
    # Exceptions
    "DoubleOError",
    "SecretError",
    "ProxyError",
    "AuthenticationError",
    "EnvError",
    # Metadata
    "__version__",
]
