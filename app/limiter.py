"""Shared slowapi Limiter instance.

Defined here (not in app.main) to avoid circular imports: routers import
this module, and app.main also imports it to attach the state and handler.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
