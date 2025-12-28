"""Top-level models package

Expose the three logical subpackages: common, public and tenant.
Callers can import models like:
  from skolo_shared import models
  from skolo_shared.models import tenant
  from skolo_shared.models.tenant import student
"""

from . import (
    common,
    public,
    tenant,
)

__all__ = [
    "common",
    "public",
    "tenant",
]
