"""Common model base exports

Expose Base, BaseModel, AuditModel, AuditUserModel and the enums from .base
so callers can `from skolo_shared.models.common import BaseModel, StatusEnum`.
"""

from .base_model import (
    Base,
    BaseModel,
    AuditModel,
    AuditUserModel,
    metadata,
    naming_convention,
    StatusBaseModel,
)
from .enums import (
    StatusEnum,
    GenderEnum,
    DeviceTypeEnum,
    OwnerTypeEnum,
    PermissionEnum,
    AttendanceStatus,
    PresentTypeEnum,
    EventNewsTypeEnum,
    PriorityEnum,
    TargetAudienceEnum,
    PaymentStatusEnum,
    RelationshipEnum,
    RoutineDayEnum,
    StaffTypeEnum,
    SalaryMonthEnum,
    CTCComponentTypeEnum,
    StudentStatusEnum,
    SubjectCategoryEnum,
    TripStatusEnum,
    UserFileTypeEnum,
    UserType,
    LoginStatus,
    LoginMethod,
    PaymentMethodEnum
)

__all__ = [
    "Base",
    "BaseModel",
    "AuditModel",
    "AuditUserModel",
    "StatusBaseModel",
    "StatusEnum",
    "GenderEnum",
    "DeviceTypeEnum",
    "OwnerTypeEnum",
    "PermissionEnum",
    "AttendanceStatus",
    "PresentTypeEnum",
    "EventNewsTypeEnum",
    "PriorityEnum",
    "TargetAudienceEnum",
    "PaymentStatusEnum",
    "RelationshipEnum",
    "RoutineDayEnum",
    "StaffTypeEnum",
    "SalaryMonthEnum",
    "CTCComponentTypeEnum",
    "StudentStatusEnum",
    "SubjectCategoryEnum",
    "TripStatusEnum",
    "UserFileTypeEnum",
    "UserType",
    "LoginStatus",
    "LoginMethod",
    "metadata",
    "naming_convention",
    "PaymentMethodEnum"
]
