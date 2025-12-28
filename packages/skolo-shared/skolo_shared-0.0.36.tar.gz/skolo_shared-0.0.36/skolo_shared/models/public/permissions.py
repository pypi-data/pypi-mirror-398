from ..common import AuditModel, Base

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Role(AuditModel):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'public'}
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(255))
    users = relationship("User", secondary="public.user_roles", back_populates="roles")
    permissions = relationship("Permission", secondary="public.role_permissions", back_populates="roles")


class Permission(AuditModel):
    __tablename__ = 'permissions'
    __table_args__ = {'schema': 'public'}
    # Make 'name' a foreign key to PermissionEnum values
    name = Column(String(255), ForeignKey('public.permission_enum_values.value'), unique=True, nullable=False)
    description = Column(String(255))
    roles = relationship("Role", secondary="public.role_permissions", back_populates="permissions")


# Create a table to store PermissionEnum values for FK constraint
class PermissionEnumValue(Base):
    __tablename__ = 'permission_enum_values'
    __table_args__ = {'schema': 'public'}
    value = Column(String(255), primary_key=True, unique=True, nullable=False)


class UserRole(Base):
    __tablename__ = 'user_roles'
    __table_args__ = {'schema': 'public'}
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('public.roles.id'), primary_key=True, nullable=False)


class RolePermission(Base):
    __tablename__ = 'role_permissions'
    __table_args__ = {'schema': 'public'}
    role_id = Column(UUID(as_uuid=True), ForeignKey('public.roles.id'), primary_key=True, nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('public.permissions.id'), primary_key=True, nullable=False)
