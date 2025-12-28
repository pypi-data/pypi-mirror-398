"""Public models package exports

Expose public model modules so callers can import modules or access models
via `from skolo_shared.models.public import user` or
`from skolo_shared.models.public.user import User`.
"""

from . import (
    permissions,
    user,
)

__all__ = [
    "permissions",
    "user",
]

