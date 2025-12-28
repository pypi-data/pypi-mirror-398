"""Tenant models package exports

Expose tenant model modules so callers can import modules or access models
via `from skolo_shared.models.tenant import student` or
`from skolo_shared.models.tenant.student import Student`.
"""

from . import (
    attendance,
    classes,
    events,
    exam,
    expenditure,
    fee,
    parent,
    payment,
    school,
    school_routine,
    staff,
    student,
    subject,
    timetable,
    tracking,
    transport,
    user_file,
    user_tenant_mapping,
    holiday,
)

__all__ = [
    "attendance",
    "classes",
    "events",
    "exam",
    "expenditure",
    "fee",
    "parent",
    "payment",
    "school",
    "school_routine",
    "staff",
    "student",
    "subject",
    "timetable",
    "tracking",
    "transport",
    "user_file",
    "user_tenant_mapping",
    "holiday",
]
