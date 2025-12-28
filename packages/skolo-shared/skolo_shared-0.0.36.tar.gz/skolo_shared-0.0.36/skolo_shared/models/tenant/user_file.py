from sqlalchemy import Column, String, DateTime, UUID, Index, Enum as SAEnum
from sqlalchemy.sql import func

from ..common import AuditModel
from ..common import OwnerTypeEnum, UserFileTypeEnum


class UserFile(AuditModel):
    __tablename__ = 'user_files'
    file_url = Column(String(1024), nullable=False)
    owner_type = Column(SAEnum(OwnerTypeEnum, name='ownertypeenum'), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    filename = Column(String(255), nullable=True)
    file_type = Column(SAEnum(UserFileTypeEnum, name='userfiletypeenum'), nullable=True,
                       server_default=UserFileTypeEnum.DOCUMENTS.value)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_userfile_owner', 'owner_type', 'owner_id'),
    )

    def __repr__(self):
        return f"<UserFile(id={self.id}, owner_type={self.owner_type}, owner_id={self.owner_id}, file_url={self.file_url})>"
