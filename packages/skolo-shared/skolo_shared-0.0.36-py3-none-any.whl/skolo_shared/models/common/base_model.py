import uuid

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declared_attr
from sqlalchemy.sql import func
from .enums import StatusEnum

# Deterministic naming convention for all constraints (PK, FK, UQ, IX, CK)
# This ensures SQLAlchemy generates stable names so Alembic can match DB vs metadata.
naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    __abstract__ = True
    # count of column  : 5
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # explicit ENUM name so DB enum type name is stable across runs
    status = Column(SAEnum(StatusEnum, name="status_enum", native_enum=True, create_type=False),
                    default=StatusEnum.ACTIVE,
                    nullable=False
                    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class StatusBaseModel(Base):
    __abstract__ = True
    status = Column(SAEnum(StatusEnum, name="status_enum", native_enum=True, create_type=False),
                    default=StatusEnum.ACTIVE,
                    nullable=False
                    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)


class AuditModel(BaseModel):
    __abstract__ = True
    # count of column  : 2 + 5 (from BaseModel) = 7
    # keep schema-qualified FK targets if your tables live in 'public'
    created_by = Column(UUID(as_uuid=True), ForeignKey("public.users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("public.users.id"), nullable=True)

    @declared_attr
    def creator(cls):
        return relationship("User", foreign_keys=[cls.created_by])

    @declared_attr
    def updater(cls):
        return relationship("User", foreign_keys=[cls.updated_by])


class AuditUserModel(AuditModel):
    __abstract__ = True
    public_user_id = Column(UUID(as_uuid=True), ForeignKey("public.users.id"))
