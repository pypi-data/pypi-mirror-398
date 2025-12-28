from ..common import AuditModel
import enum
from sqlalchemy import Column, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from ..common.enums import TenantTypeEnum


class UserTenantMapping(AuditModel):
    __tablename__ = 'user_tenant_mapping'
    public_user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=False, index=True)
    user_type = Column(Enum(TenantTypeEnum), nullable=False)
    tenant_user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Note: No ForeignKey constraint at DB level for tenant_user_id due to polymorphic reference

    def __repr__(self):
        return f"<UserTenantMapping(id={self.id}, public_user_id={self.public_user_id}, user_type={self.user_type}, tenant_user_id={self.tenant_user_id})>"
